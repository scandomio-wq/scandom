(function(){
  const ICONS = {
    // Zones
    Hall: '🏠',
    Couloir: '➡️',
    Ascenseur: '🛗',
    Escalier: '🪜',
    'Façade': '🏢',
    'Boîtes aux lettres': '📬',
    'Local vélos': '🚲',
    'Local technique': '⚙️',
    'Cour / Jardin': '🌳',
    Autre: '⋯',
    // Catégories
    'Électricité': '🔌',
    'Propreté': '🧹',
    'Plomberie': '🚰',
    'Porte / Fenêtre': '🪟',
    'Consommable': '📦'
  };
  

  function buildPills(containerId, groupName, onSelect){
    const root = document.getElementById(containerId);
    if(!root) return null;
    const radios = Array.from(root.querySelectorAll('label.radio-option input[type="radio"]'));
    if(radios.length === 0) return null;

    // Create pills container
    const pills = document.createElement('div');
    pills.className = 'pills-container';
    pills.id = containerId + 'Pills';

    radios.forEach(input => {
      const labelText = (input.nextElementSibling && input.nextElementSibling.textContent.trim()) || '';
      const value = input.value;

      const pill = document.createElement('div');
      pill.className = 'pill';
      pill.setAttribute('data-group', groupName);
      pill.setAttribute('data-value', value);

      const iconSpan = document.createElement('span');
      iconSpan.textContent = ICONS[labelText] || '•';
      iconSpan.setAttribute('aria-hidden','true');
      iconSpan.style.marginRight = '8px';

      const textSpan = document.createElement('span');
      textSpan.textContent = labelText;

      pill.appendChild(iconSpan);
      pill.appendChild(textSpan);

      pill.addEventListener('click', () => {
        console.log('[pills.js] click (built pill)', {group: groupName, value, label: labelText});
        // unselect same group
        pills.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
        pill.classList.add('selected');

        // update underlying state + visual summary
        try {
          const numeric = parseInt(value,10);
          if(groupName === 'zoneSimple' || groupName === 'zoneAdvanced'){
            if(typeof window.selectedZone !== 'undefined') window.selectedZone = numeric;
            if(typeof window.updateZoneSelected === 'function'){
              const lbl = (window.zoneLabels && window.zoneLabels[numeric]) || labelText;
              window.updateZoneSelected(lbl);
            }
          } else if(groupName === 'catSimple' || groupName === 'catAdvanced'){
            if(typeof window.selectedCategorie !== 'undefined') window.selectedCategorie = numeric;
            if(typeof window.updateCategorieSelected === 'function'){
              const lbl = (window.categorieLabels && window.categorieLabels[numeric]) || labelText;
              window.updateCategorieSelected(lbl);
            }
            if (typeof window.renderIncidentRadios === 'function') {
              window.renderIncidentRadios();
            }
          }
        } catch(e) { /* noop */ }
      });

      // preselect if radio was checked
      if(input.checked){
        pill.classList.add('selected');
      }

      pills.appendChild(pill);
    });

    // Hide original radio group and insert pills
    root.style.display = 'none';
    root.insertAdjacentElement('afterend', pills);

    return pills;
  }

  function mirrorToggle(btnId, showId, hideId){
    const btn = document.getElementById(btnId);
    if(!btn) return;
    btn.addEventListener('click', () => {
      const show = document.getElementById(showId + 'Pills');
      const hide = document.getElementById(hideId + 'Pills');
      if(show) show.style.display = 'block';
      if(hide) hide.style.display = 'none';
    });
  }

  function clearAllPills(){
    document.querySelectorAll('.pill.selected').forEach(p => p.classList.remove('selected'));
    const z = document.getElementById('zoneSelected');
    if(z) z.textContent = '—';
    const c = document.getElementById('categorieSelected');
    if(c) c.textContent = '—';
    const i = document.getElementById('incidentSelected');
    if(i) i.textContent = '—';
  }

  function init(){
    // Ensure icons exist on any pre-defined pills in HTML (e.g. Zone section)
    document.querySelectorAll('.pill[data-group]').forEach(pill => {
      const group = pill.getAttribute('data-group');
      if(group === 'zoneSimple' || group === 'zoneAdvanced'){
        // Derive label from last span or text
        const label = (pill.querySelector('span:last-child')?.textContent || pill.textContent || '').trim();
        // Remove any <i> placeholders left in HTML
        pill.querySelectorAll('i').forEach(i => i.remove());
        // If no leading icon span yet, prepend one
        const hasIcon = pill.firstElementChild && pill.firstElementChild.tagName.toLowerCase() === 'span' && pill.firstElementChild.getAttribute('aria-hidden') === 'true';
        if(!hasIcon){
          const iconSpan = document.createElement('span');
          iconSpan.textContent = ICONS[label] || '•';
          iconSpan.setAttribute('aria-hidden','true');
          iconSpan.style.marginRight = '8px';
          pill.insertBefore(iconSpan, pill.firstChild);
        }
      }
    });

    // Build for the four groups if present
    const zSimple = buildPills('zoneSimple','zoneSimple');
    const zAdv   = buildPills('zoneAdvanced','zoneAdvanced');
    const cSimple = buildPills('catSimple','catSimple');
    const cAdv   = buildPills('catAdvanced','catAdvanced');

    // Also bind to any pre-existing .pill elements already in the HTML
    // (e.g., Zone section where pills are hardcoded)
    document.querySelectorAll('.pill[data-group][data-value]').forEach(pill => {
      // Skip if already has a listener added by buildPills (same behavior)
      if (pill.__pbind) return;
      pill.__pbind = true;

      pill.addEventListener('click', () => {
        const group = pill.getAttribute('data-group');
        const value = parseInt(pill.getAttribute('data-value'), 10);
        const label = (pill.querySelector('span:last-child')?.textContent || pill.textContent || '').trim();
        console.log('[pills.js] click (existing pill)', {group, value, label});

        // Unselect within same group (search globally, not just siblings)
        document.querySelectorAll(`.pill[data-group="${group}"]`).forEach(p => p.classList.remove('selected'));
        pill.classList.add('selected');

        // Update state and headings
        try {
          if(group === 'zoneSimple' || group === 'zoneAdvanced'){
            if(typeof window.setSelectedZone === 'function') window.setSelectedZone(value);
            if(typeof window.updateZoneSelected === 'function'){
              const lbl = (window.zoneLabels && window.zoneLabels[value]) || label;
              window.updateZoneSelected(lbl);
            }
          } else if(group === 'catSimple' || group === 'catAdvanced'){
            if(typeof window.setSelectedCategorie === 'function') window.setSelectedCategorie(value);
            if(typeof window.updateCategorieSelected === 'function'){
              const lbl = (window.categorieLabels && window.categorieLabels[value]) || label;
              window.updateCategorieSelected(lbl);
            }
            if (typeof window.renderIncidentRadios === 'function') {
              window.renderIncidentRadios();
            }
          }
        } catch(e) { /* noop */ }
      });
    });

    // Default visibility mirrors the original
    if(zSimple && zAdv){
      if(document.getElementById('zoneAdvanced').style.display === 'none'){
        zSimple.style.display = 'flex';
        zAdv.style.display = 'none';
      } else {
        zSimple.style.display = 'none';
        zAdv.style.display = 'block';
      }
    }
    if(cSimple && cAdv){
      if(document.getElementById('catAdvanced').style.display === 'none'){
        cSimple.style.display = 'flex';
        cAdv.style.display = 'none';
      } else {
        cSimple.style.display = 'none';
        cAdv.style.display = 'block';
      }
    }

    // Mirror existing toggle buttons
    mirrorToggle('btnZoneMore','zoneAdvanced','zoneSimple');
    mirrorToggle('btnZoneLess','zoneSimple','zoneAdvanced');
    mirrorToggle('btnCatMore','catAdvanced','catSimple');
    mirrorToggle('btnCatLess','catSimple','catAdvanced');

    // Keep categories unselected on load; user must explicitly choose.

    // Wrap resetForm if present to also clear pills
    if(typeof window.resetForm === 'function'){
      const originalReset = window.resetForm;
      window.resetForm = function(){
        try { originalReset(); } catch(e){}
        clearAllPills();
      }
    }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
