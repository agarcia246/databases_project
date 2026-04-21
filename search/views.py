from django.shortcuts import render

from .services import hydrate_products, semantic_search


def product_search(request):
    q = request.GET.get('q', '').strip()
    raw_k = request.GET.get('k', '10')
    try:
        k = max(1, min(50, int(raw_k)))
    except ValueError:
        k = 10

    results = hydrate_products(semantic_search(q, k=k)) if q else []

    return render(request, 'search/product_search.html', {
        'active_nav': 'search',
        'q': q,
        'k': k,
        'results': results,
    })
