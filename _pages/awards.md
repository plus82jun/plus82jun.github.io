---
layout: archive
title: "Awards"
permalink: /awards/
author_profile: true
---

<!-- Award entries live in _data/awards.yml. Add a new block there; this page needs no edits. -->

<ol class="award-grid">
{%- for award in site.data.awards %}
  <li class="award-grid__item">
    <button type="button" class="award-card"
      data-title="{{ award.title | escape }}"
      data-org="{{ award.org | escape }}"
      data-date="{{ award.date | escape }}"
      data-description="{{ award.description | escape }}"
      data-image="{{ award.image | relative_url }}">
      <span class="award-card__thumb">
        <img src="{{ award.thumb | relative_url }}" alt="{{ award.title | escape }} certificate" loading="lazy">
        <span class="award-card__no">{{ forloop.index }}</span>
      </span>
      <span class="award-card__title">{{ award.title }}</span>
      <span class="award-card__date">{{ award.date }}</span>
    </button>
  </li>
{%- endfor %}
</ol>

<div class="award-modal" id="award-modal" role="dialog" aria-modal="true" aria-labelledby="award-modal-title" hidden>
  <div class="award-modal__panel">
    <button type="button" class="award-modal__close" aria-label="Close">&times;</button>
    <img class="award-modal__img" id="award-modal-img" src="" alt="">
    <div class="award-modal__info">
      <h2 id="award-modal-title"></h2>
      <p class="award-modal__org" id="award-modal-org"></p>
      <p class="award-modal__date" id="award-modal-date"></p>
      <p class="award-modal__desc" id="award-modal-desc"></p>
    </div>
  </div>
</div>

<script>
(function () {
  var modal = document.getElementById('award-modal');
  if (!modal) { return; }
  var img = document.getElementById('award-modal-img');
  var titleEl = document.getElementById('award-modal-title');
  var orgEl = document.getElementById('award-modal-org');
  var dateEl = document.getElementById('award-modal-date');
  var descEl = document.getElementById('award-modal-desc');
  var closeBtn = modal.querySelector('.award-modal__close');
  var lastFocus = null;

  function openModal(card) {
    lastFocus = card;
    img.src = card.getAttribute('data-image');
    img.alt = card.getAttribute('data-title') + ' certificate';
    titleEl.textContent = card.getAttribute('data-title');
    orgEl.textContent = card.getAttribute('data-org');
    dateEl.textContent = card.getAttribute('data-date');
    descEl.textContent = card.getAttribute('data-description');
    modal.hidden = false;
    document.documentElement.classList.add('award-modal-open');
    closeBtn.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.documentElement.classList.remove('award-modal-open');
    img.src = '';
    if (lastFocus) { lastFocus.focus(); }
  }

  var cards = document.querySelectorAll('.award-card');
  for (var i = 0; i < cards.length; i++) {
    cards[i].addEventListener('click', function () { openModal(this); });
  }
  closeBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) { closeModal(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) { closeModal(); }
  });
})();
</script>
