/*
SHESTAR BROWSER JAVASCRIPT
==========================
Small browser interactions live here, especially the right-side drawer.
Database/order logic stays in Python.
*/

(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];

  function getCookie(name){
    const row = document.cookie.split('; ').find(x => x.startsWith(name + '='));
    return row ? decodeURIComponent(row.split('=').slice(1).join('=')) : '';
  }
  function showToast(text){
    const el = $('[data-toast]'); if(!el) return;
    el.textContent = text; el.classList.add('show');
    clearTimeout(window.__shestarToast); window.__shestarToast = setTimeout(()=>el.classList.remove('show'), 2200);
  }
  function setCartCount(count){ $$('[data-cart-count]').forEach(el => el.textContent = count); }
  function money(value){ return new Intl.NumberFormat('fa-IR').format(Number(value || 0)) + ' تومان'; }

  const drawer = $('[data-mobile-menu]');
  const scrim = $('[data-drawer-scrim]');
  const menuButton = $('[data-menu-open]');
  function openMenu(){
    if(!drawer) return;
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden','false');
    menuButton?.setAttribute('aria-expanded','true');
    scrim.hidden=false;
    document.body.classList.add('no-scroll');
    $('[data-menu-close]')?.focus({preventScroll:true});
  }
  function closeMenu(){
    if(!drawer) return;
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden','true');
    menuButton?.setAttribute('aria-expanded','false');
    scrim.hidden=true;
    document.body.classList.remove('no-scroll');
  }
  menuButton?.addEventListener('click', openMenu);
  $('[data-menu-close]')?.addEventListener('click', closeMenu);
  scrim?.addEventListener('click', closeMenu);
  drawer?.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', (event) => { if(event.key === 'Escape' && drawer?.classList.contains('open')) closeMenu(); });

  $$('.message button').forEach(btn => btn.addEventListener('click', () => btn.parentElement.remove()));

  $$('[data-gallery-src]').forEach(btn => btn.addEventListener('click', () => {
    const main = $('[data-main-product-image]'); if(main) main.src = btn.dataset.gallerySrc;
  }));

  $$('[data-copy]').forEach(btn => btn.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(btn.dataset.copy); showToast('کپی شد'); }
    catch(_) { showToast('امکان کپی خودکار نبود'); }
  }));

  $('[data-filter-toggle]')?.addEventListener('click', () => $('.filters')?.classList.toggle('mobile-open'));

  $$('.js-add-cart').forEach(form => form.addEventListener('submit', async (event) => {
    const selected = form.querySelector('input[name="variant_id"]:checked');
    if(!selected){ event.preventDefault(); showToast('اول سایز را انتخاب کن'); return; }
    if(!window.fetch || !window.SHESTAR?.addUrl) return;
    event.preventDefault();
    try{
      const res = await fetch(window.SHESTAR.addUrl, {
        method:'POST',
        headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRFToken':getCookie('csrftoken')},
        body:JSON.stringify({variant_id:Number(selected.value), quantity:1})
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error || 'خطایی رخ داد');
      setCartCount(data.count || 0); showToast('به سبد خرید اضافه شد');
    }catch(err){ showToast(err.message); }
  }));

  const checkout = $('[data-checkout-form]');
  if(checkout){
    const standard = Number(checkout.dataset.standardFee || 0), express = Number(checkout.dataset.expressFee || 0);
    const threshold = Number(checkout.dataset.freeThreshold || 0), merchandise = Number(checkout.dataset.merchandiseTotal || 0);
    const refresh = () => {
      const selected = checkout.querySelector('input[name="shipping_method"]:checked');
      let fee = selected?.value === 'express' ? express : standard;
      if(threshold > 0 && merchandise >= threshold) fee = 0;
      const feeEl = $('[data-shipping-preview]', checkout), totalEl = $('[data-grand-total]', checkout);
      if(feeEl) feeEl.textContent = money(fee); if(totalEl) totalEl.textContent = money(merchandise + fee);
    };
    checkout.querySelectorAll('input[name="shipping_method"]').forEach(el => el.addEventListener('change', refresh)); refresh();
  }
})();
