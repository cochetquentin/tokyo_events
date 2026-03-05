// Tokyo Events Map - Alpine.js Application
// ==========================================

document.addEventListener('alpine:init', () => {
  // Main Filters Store
  Alpine.store('filters', {
    // State
    selectedCategories: new Set(),
    allCategoriesMetadata: {},
    dateFrom: '',
    dateTo: '',
    loading: false,
    error: null,

    // Initialization
    async init() {
      // Set today's date by default
      const today = new Date().toISOString().split('T')[0];
      this.dateFrom = today;
      this.dateTo = today;

      // Load categories metadata
      await this.loadCategoriesMetadata();

      // Initial data load
      await this.applyFilters();
    },

    // Load categories metadata from API
    async loadCategoriesMetadata() {
      try {
        const response = await fetch('/api/events/all-categories');
        this.allCategoriesMetadata = await response.json();
      } catch (error) {
        console.error('Error loading categories metadata:', error);
        this.showError('Erreur lors du chargement des catégories');
      }
    },

    // Toggle category selection
    toggleCategory(key) {
      if (this.selectedCategories.has(key)) {
        this.selectedCategories.delete(key);
      } else {
        this.selectedCategories.add(key);
      }
      // Trigger reactivity
      this.selectedCategories = new Set(this.selectedCategories);

      // Apply filters with debounce
      this.debouncedApplyFilters();
    },

    // Check if category is selected
    isCategorySelected(key) {
      return this.selectedCategories.has(key);
    },

    // Set date range (today, week, month)
    setDateRange(range) {
      const today = new Date();
      let startDate, endDate;

      switch(range) {
        case 'today':
          startDate = endDate = today;
          break;
        case 'week':
          startDate = today;
          endDate = new Date(today);
          endDate.setDate(today.getDate() + 6);
          break;
        case 'month':
          startDate = today;
          endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
          break;
        default:
          return;
      }

      this.dateFrom = startDate.toISOString().split('T')[0];
      this.dateTo = endDate.toISOString().split('T')[0];

      this.applyFilters();
    },

    // Reset all filters
    resetFilters() {
      const today = new Date().toISOString().split('T')[0];
      this.dateFrom = today;
      this.dateTo = today;
      this.selectedCategories = new Set();
      this.applyFilters();
    },

    // Build query params from current filters
    buildQueryParams() {
      const params = new URLSearchParams();

      // Separate selected categories by filter_type
      const eventTypes = [];
      const categoryGroups = [];

      for (const key of this.selectedCategories) {
        const meta = this.allCategoriesMetadata[key];
        if (!meta) continue;

        if (meta.filter_type === 'event_type') {
          eventTypes.push(meta.filter_value || key);
        } else if (meta.filter_type === 'category_group') {
          categoryGroups.push(key);
        }
      }

      // Add event_types param
      if (eventTypes.length > 0) {
        params.append('event_types', eventTypes.join(','));
      }

      // Add category_groups param
      if (categoryGroups.length > 0) {
        params.append('category_groups', categoryGroups.join(','));
      }

      // Add date params
      if (this.dateFrom) {
        params.append('start_date_from', this.dateFrom.replace(/-/g, '/'));
      }
      if (this.dateTo) {
        params.append('start_date_to', this.dateTo.replace(/-/g, '/'));
      }

      return params;
    },

    // Apply filters - update map, stats, and events list
    async applyFilters() {
      this.loading = true;
      this.error = null;

      try {
        await Promise.all([
          this.updateMap(),
          Alpine.store('stats').load(),
          Alpine.store('events').load()
        ]);
      } catch (error) {
        console.error('Error applying filters:', error);
        this.showError('Erreur lors de l\'application des filtres');
      } finally {
        this.loading = false;
      }
    },

    // Debounced apply filters (for date inputs)
    debouncedApplyFilters: debounce(function() {
      this.applyFilters();
    }, 500),

    // Update map iframe
    updateMap() {
      const params = this.buildQueryParams();
      const newUrl = `/api/map/generate?${params.toString()}`;

      // Force reload iframe with timestamp
      const iframe = document.getElementById('mapFrame');
      if (iframe) {
        iframe.src = newUrl + (newUrl.includes('?') ? '&' : '?') + '_t=' + Date.now();
      }
    },

    // Show error message
    showError(message) {
      this.error = message;
      // Auto-dismiss after 5s
      setTimeout(() => {
        this.error = null;
      }, 5000);
    },

    // Show success message
    showSuccess(message) {
      // Réutilisation du système error pour afficher le succès
      this.error = message;
      setTimeout(() => {
        this.error = null;
      }, 5000);
    }
  });

  // Stats Store
  Alpine.store('stats', {
    totalEvents: 0,
    byType: {},
    byCategoryGroup: {},
    loading: false,

    async load() {
      this.loading = true;
      const filters = Alpine.store('filters');
      const params = filters.buildQueryParams();

      try {
        const response = await fetch(`/api/events/stats?${params.toString()}`);
        const data = await response.json();

        this.totalEvents = data.total_events || 0;
        this.byType = data.by_type || {};
        this.byCategoryGroup = data.by_category_group || {};
      } catch (error) {
        console.error('Error loading stats:', error);
      } finally {
        this.loading = false;
      }
    },

    // Get count for a specific category
    getCategoryCount(key) {
      const filters = Alpine.store('filters');
      const meta = filters.allCategoriesMetadata[key];

      if (!meta) return 0;

      if (meta.filter_type === 'event_type') {
        const typeKey = meta.filter_value || key;
        return this.byType[typeKey] || 0;
      } else if (meta.filter_type === 'category_group') {
        return this.byCategoryGroup[key] || 0;
      }

      return 0;
    }
  });

  // Events Store
  Alpine.store('events', {
    events: [],
    groupedEvents: {},
    loading: false,

    async load() {
      this.loading = true;
      const filters = Alpine.store('filters');
      const params = filters.buildQueryParams();

      try {
        const response = await fetch(`/api/events?${params.toString()}`);
        const data = await response.json();

        this.events = data.events || [];
        this.groupedEvents = this.groupByType(this.events);
      } catch (error) {
        console.error('Error loading events:', error);
      } finally {
        this.loading = false;
      }
    },

    // Group events by type
    groupByType(events) {
      const grouped = {
        'hanabi': [],
        'festivals': [],
        'expositions': [],
        'marches': [],
        'tokyo_cheapo': []
      };

      events.forEach(event => {
        if (grouped[event.event_type]) {
          grouped[event.event_type].push(event);
        }
      });

      return grouped;
    },

    // Get icon for event type
    getTypeIcon(type) {
      const icons = {
        'hanabi': 'fire',
        'festivals': 'music',
        'expositions': 'palette',
        'marches': 'store',
        'tokyo_cheapo': 'globe'
      };
      return icons[type] || 'calendar';
    },

    // Get label for event type
    getTypeLabel(type) {
      const labels = {
        'hanabi': 'Hanabi',
        'festivals': 'Festivals',
        'expositions': 'Expositions',
        'marches': 'Marchés',
        'tokyo_cheapo': 'Tokyo Cheapo'
      };
      return labels[type] || type;
    },

    // Get color for event type
    getTypeColor(type) {
      const colors = {
        'hanabi': '#ff6b35',
        'festivals': '#ff385c',
        'expositions': '#5b7fff',
        'marches': '#00c896',
        'tokyo_cheapo': '#42a5f5'
      };
      return colors[type] || '#0d6efd';
    },

    // Focus on a specific event
    focusOnEvent(lat, lon, name) {
      const filters = Alpine.store('filters');
      const params = filters.buildQueryParams();

      params.append('center_lat', lat);
      params.append('center_lon', lon);
      params.append('zoom', 15);

      const iframe = document.getElementById('mapFrame');
      if (iframe) {
        iframe.src = `/api/map/generate?${params.toString()}`;
      }
    }
  });

  // Update Status Store
  Alpine.store('updateStatus', {
    // État
    status: 'idle', // 'idle' | 'running' | 'cooldown' | 'success' | 'error'
    taskId: null,
    results: null,
    error: null,
    cooldownRemaining: 0,
    cooldownTimer: null,
    pollingInterval: null,

    // Initialisation
    async init() {
      await this.checkCooldownStatus();
    },

    // Vérifier le statut du cooldown au chargement
    async checkCooldownStatus() {
      try {
        const response = await fetch('/api/events/update/cooldown');
        const data = await response.json();

        if (data.cooldown_active) {
          this.status = 'cooldown';
          this.cooldownRemaining = data.remaining_seconds;
          this.startCooldownTimer();
        }
      } catch (error) {
        console.error('Erreur lors de la vérification du cooldown:', error);
      }
    },

    // Déclencher la mise à jour
    async triggerUpdate() {
      if (this.status === 'running' || this.status === 'cooldown') {
        return;
      }

      this.status = 'running';
      this.error = null;

      try {
        const response = await fetch('/api/events/update', {
          method: 'POST'
        });
        const data = await response.json();

        if (data.error) {
          this.status = 'cooldown';
          this.cooldownRemaining = data.retry_after;
          this.startCooldownTimer();
          return;
        }

        this.taskId = data.task_id;
        this.pollStatus();
      } catch (error) {
        this.status = 'error';
        this.error = 'Erreur de connexion au serveur';
      }
    },

    // Polling du statut de la tâche
    pollStatus() {
      this.pollingInterval = setInterval(async () => {
        try {
          const response = await fetch(`/api/events/update/status/${this.taskId}`);
          const data = await response.json();

          if (data.status === 'completed') {
            clearInterval(this.pollingInterval);
            this.status = 'success';
            this.results = data.results;
            await this.onUpdateComplete();
          } else if (data.status === 'error') {
            clearInterval(this.pollingInterval);
            this.status = 'error';
            this.error = data.error;
          }
        } catch (error) {
          clearInterval(this.pollingInterval);
          this.status = 'error';
          this.error = 'Erreur lors de la vérification du statut';
        }
      }, 2000); // Poll toutes les 2 secondes
    },

    // Gestion du timer de cooldown
    startCooldownTimer() {
      if (this.cooldownTimer) {
        clearInterval(this.cooldownTimer);
      }

      this.cooldownTimer = setInterval(() => {
        this.cooldownRemaining--;
        if (this.cooldownRemaining <= 0) {
          clearInterval(this.cooldownTimer);
          this.status = 'idle';
          this.cooldownTimer = null;
        }
      }, 1000);
    },

    // Callback après succès
    async onUpdateComplete() {
      // Afficher la modal de résultats
      const modal = new bootstrap.Modal(document.getElementById('updateResultsModal'));
      modal.show();

      // Rafraîchir les données (carte + liste + stats)
      await Alpine.store('filters').applyFilters();

      // Démarrer le cooldown
      this.cooldownRemaining = 300; // 5 minutes
      this.status = 'cooldown';
      this.startCooldownTimer();
    },

    // Formater le temps de cooldown
    formatCooldown() {
      const minutes = Math.floor(this.cooldownRemaining / 60);
      const seconds = this.cooldownRemaining % 60;
      return `${minutes}m ${seconds}s`;
    }
  });
});

// Utility: Debounce function
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  // Wait for Alpine to be ready
  if (window.Alpine) {
    Alpine.store('filters').init();
    Alpine.store('updateStatus').init();
  }
});
