# Documentation Technique — Scraper Tokyo Cheapo Events
## tokyocheapo.com/events/
---
## 1. Vue d'ensemble du site
**URL de base :** `https://tokyocheapo.com/events/`
Le site Tokyo Cheapo est un site WordPress. La page événements affiche une liste paginée
de cartes (cards). Chaque carte contient un résumé. Un clic mène à une page de détail
beaucoup plus riche.
**Stratégie recommandée :**
1. Parcourir toutes les pages de la liste pour collecter les URLs
2. Visiter chaque page de détail pour extraire les données complètes
---
## 2. Architecture des URLs
### 2.1 Pages liste (index)
| Description              | URL                                                        |
|--------------------------|------------------------------------------------------------|
| Tous les événements p.1  | `https://tokyocheapo.com/events/`                          |
| Page 2, 3...             | `https://tokyocheapo.com/events/page/2/`                   |
| Filtre par mois          | `https://tokyocheapo.com/events/march`                     |
| Filtre semaine courante  | `https://tokyocheapo.com/events/this-week`                 |
| Filtre mois courant      | `https://tokyocheapo.com/events/this-month`                |
| Par catégorie            | `https://tokyocheapo.com/event-category/festival`          |
| Par lieu                 | `https://tokyocheapo.com/events/location/central-tokyo/shibuya-2/` |
**Mois disponibles (slugs) :**
`march` · `april` · `may` · `june` · `july` · `august` ·
`september` · `october` · `november` · `december` · `january` · `february`
**Format pagination :**
- Page 1 : `https://tokyocheapo.com/events/`
- Page N : `https://tokyocheapo.com/events/page/{N}/`
### 2.2 Pages de détail
Format : `https://tokyocheapo.com/events/{slug-de-l-evenement}/`
Exemple : `https://tokyocheapo.com/events/matsuda-cherry-blossom-festival/`
---
## 3. Structure HTML — Page Liste
### 3.1 Conteneur principal des événements
```html
<ul class="grid">
  <li>
    <article class="article card card--event [featured]">
      ...
    </article>
  </li>
  <!-- ATTENTION : certains <li> NE SONT PAS des événements -->
  <!-- li.cheapo-preview = encart publicitaire                -->
  <!-- li.none / li.basic = hôtels recommandés               -->
</ul>
```
**Sélecteur correct :** `article.card--event`
(filtre automatiquement les non-événements)
**Nombre d'événements par page :** ~24 articles
### 3.2 Structure complète d'une card événement
```html
<article class="article card card--event [featured]">
  <!-- ── BLOC IMAGE + DATE ── -->
  <a class="card__image"
     data-post-id="323395"
     href="https://tokyocheapo.com/events/{slug}/"
     title="{Nom de l'événement}">
    <img src="..." class="cheapo-archive-thumb" width="362" height="193">
    <div class="card__image__overlay">
      <div class="card__image__overlay__content">
        <!-- DATE BOX — 3 variantes possibles -->
        <!-- VARIANTE 1 : plage de dates, même année -->
        <div class="card--event__date-box multi">
          <div class="inner">
            <div class="date">Feb 28</div>
            <div class="tilde">~</div>
            <div class="date">Mar 1</div>
          </div>
        </div>
        <!-- VARIANTE 2 : plage de dates, années différentes -->
        <div class="card--event__date-box multi multi-year">
          <div class="inner">
            <div class="date">Nov 17</div>
            <div class="tilde">~</div>
            <div class="date">Mar 1 2026</div>  <!-- année explicite -->
          </div>
        </div>
        <!-- VARIANTE 3 : date unique -->
        <div class="card--event__date-box single">
          <div class="inner">
            <div class="day">Sun, Mar</div>  <!-- jour semaine + mois -->
            <div class="date">01</div>        <!-- numéro du jour SEULEMENT -->
          </div>
        </div>
        <!-- Label featured (optionnel) -->
        <div class="sponsored-label">Featured</div>
      </div>
    </div>
  </a>
  <!-- ── BLOC CONTENU ── -->
  <div class="card__content">
    <!-- Titre + description courte -->
    <div>
      <h3 class="card__title">
        <a href="https://tokyocheapo.com/events/{slug}/"
           title="{Nom}"
           data-post-id="{id}">
          Nom de l'événement
        </a>
      </h3>
      <p class="card__excerpt">Description courte (1 phrase).</p>
      <div class="card__cta">
        <a class="button button--secondary button--small" href="...">Read more</a>
      </div>
    </div>
    <!-- Attributs de l'événement -->
    <div>
      <!-- ATTRIBUT HEURE -->
      <div class="card--event__attribute">
        <div class="cheapo-icon" title="Start/end time">  <!-- ← clé d'identification -->
          <svg>...</svg>
        </div>
        <span>9:00am – 4:00pm</span>  <!-- valeur dans un <span> -->
      </div>
      <!-- ATTRIBUT PRIX -->
      <div class="card--event__attribute">
        <div class="cheapo-icon" title="Entry">  <!-- ← clé d'identification -->
          <svg class="svg-inline--fa fa-coins ...">...</svg>
        </div>
        ¥500 (at the door)   <!-- valeur en texte DIRECT (pas de <span>) -->
        <!-- OU : Free -->
      </div>
      <!-- ATTRIBUT CATÉGORIE -->
      <div class="card--event__attribute">
        <div class="cheapo-icon" title="Category">  <!-- ← clé d'identification -->
          <svg>...</svg>
        </div>
        <a href="https://tokyocheapo.com/event-category/festival">Festival</a>
      </div>
      <!-- LOCALISATION (badge séparé) -->
      <div class="card__category label">
        <a href="https://tokyocheapo.com/events/location/.../">Matsuda</a>
        <img>  <!-- icône épingle -->
      </div>
    </div>
  </div>
</article>
```
> **Point critique :** L'attribut `title` du `div.cheapo-icon` est la seule façon
> fiable de distinguer heure / prix / catégorie. Valeurs possibles :
> `"Start/end time"`, `"Entry"`, `"Category"`.
### 3.3 Pagination
```html
<nav class="post-nav">
  <div class="post-previous"><a href="...">«</a></div>
  <div class="post-page ">          <!-- page non-courante -->
    <a href="https://tokyocheapo.com/events/">1</a>
  </div>
  <div class="post-page current">   <!-- page courante -->
    <a href="https://tokyocheapo.com/events/page/2/">2</a>
  </div>
  <div class="post-page ">
    <a href="https://tokyocheapo.com/events/page/3/">3</a>
  </div>
  ...
  <div class="post-next"><a href="...">»</a></div>
</nav>
```
**Récupération du nombre total de pages :**
```python
nav = soup.select_one("nav.post-nav")
page_links = nav.select(".post-page a")
max_page = max([int(a.text) for a in page_links if a.text.strip().isdigit()])
```
---
## 4. Structure HTML — Page de Détail
### 4.1 Article principal
La classe de l'`<article>` contient des métadonnées WordPress utiles :
```html
<article class="post-323395 event type-event status-publish
                has-post-thumbnail location-matsuda event-category-festival
                event-tag-cherry-blossom">
```
On peut en extraire : `location-{slug}`, `event-category-{slug}`, `event-tag-{slug}`.
### 4.2 En-tête de l'événement
```html
<header class="article__header--event">
  <!-- Date box (mêmes 3 variantes que la liste) -->
  <div class="article__header--event__date-box">
    <div class="inner">
      <div class="date">Feb 14</div>
      <div class="tilde">~</div>
      <div class="date">Mar 8</div>
    </div>
  </div>
  <!-- Titre principal -->
  <h1 class="article__header--event__title">
    Matsuda Cherry Blossom Festival
  </h1>
  <!-- Attributs (même logique que les cards) -->
  <div class="event__attribute">
    <div class="cheapo-icon" title="Start/end time">...</div>
    <span>9:00am – 4:00pm</span>
  </div>
  <div class="event__attribute">
    <div class="cheapo-icon" title="Entry">...</div>
    ¥500 (at the door)
  </div>
  <div class="card--event__attribute">
    <div class="cheapo-icon" title="Category">...</div>
    <a href="/event-category/festival">Festival</a>
  </div>
  <!-- Localisation -->
  <a href="https://tokyocheapo.com/locations/.../">Matsuda</a>
  <!-- Bouton calendrier -->
  <button>Add to Calendar</button>
</header>
```
### 4.3 Section info-box ← SOURCE PRINCIPALE DE DONNÉES