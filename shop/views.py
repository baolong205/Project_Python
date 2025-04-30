# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, Category, Order, OrderItem, Review
from .forms import ProductForm, CheckoutForm, ReviewForm

# Trang chủ + tìm kiếm/lọc
def superuser_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_superuser)(view_func))

def home(request):
    categories = Category.objects.all()
    qs = Product.objects.all()
    # Tìm kiếm & lọc cơ bản
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    rating_min = request.GET.get('rating_min', '')

    if q:
        qs = qs.filter(name__icontains=q)
    if cat:
        qs = qs.filter(category__id=cat)
    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)
    if rating_min:
        qs = qs.filter(rating__gte=rating_min)

    return render(request, 'shop/product_list.html', {
        'products': qs,
        'categories': categories,
        'q': q,
        'category_filter': cat,
        'price_min': price_min,
        'price_max': price_max,
        'rating_min': rating_min,
    })

# Hiển thị sản phẩm theo danh mục
def category_products(request, slug):
    categories = Category.objects.all()
    cat = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=cat)
    return render(request, 'shop/product_list.html', {
        'categories': categories,
        'products': products,
        'current_category': slug,
        'q': '',
        'category_filter': '',
        'price_min': '',
        'price_max': '',
        'rating_min': '',
    })

# Chi tiết sản phẩm + đánh giá
def product_detail(request, product_id):
    product     = get_object_or_404(Product, id=product_id)
    reviews     = product.reviews.select_related('user').all()
    review_form = ReviewForm()

    # Xử lý gửi review
    if request.method == 'POST' and 'submit_review' in request.POST:
        if not request.user.is_authenticated:
            return redirect('login')
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            rev = review_form.save(commit=False)
            rev.product = product
            rev.user    = request.user
            rev.save()
            return redirect('product_detail', product_id=product.id)

    return render(request, 'shop/product_detail.html', {
        'product':      product,
        'reviews':      reviews,
        'review_form':  review_form,
    })

# Giỏ hàng (session-based)
def cart_view(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        pid = str(request.POST.get('product_id'))
        qty = int(request.POST.get('quantity', 1))
        cart[pid] = cart.get(pid, 0) + qty
        request.session['cart'] = cart
        return redirect('cart')

    items, total = [], 0
    for pid, qty in cart.items():
        product    = get_object_or_404(Product, id=pid)
        line_total = product.price * qty
        items.append({
            'product':        product,
            'quantity':       qty,
            'price_vnd':      product.price_vnd,
            'line_total_vnd': f"{int(line_total):,}".replace(",", ".") + " VND",
        })
        total += line_total

    total_vnd = f"{int(total):,}".replace(",", ".") + " VND"
    return render(request, 'shop/cart.html', {
        'items':      items,
        'total':      total,
        'total_vnd':  total_vnd,
    })

# Checkout & tạo đơn
@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            pm = form.cleaned_data['payment_method']
            order = Order.objects.create(
                user=         request.user,
                full_name=    form.cleaned_data['full_name'],
                address=      form.cleaned_data['address'],
                city=         form.cleaned_data['city'],
                postal_code=  form.cleaned_data['postal_code'],
                payment_method=pm,
                paid=           (pm != 'cod'),
                status=         ('awaiting_shipment' if pm in ('bank','card') else 'pending'),
            )
            for pid, qty in cart.items():
                product = get_object_or_404(Product, id=pid)
                OrderItem.objects.create(
                    order=    order,
                    product=  product,
                    price=    product.price,
                    quantity= qty,
                )
            del request.session['cart']
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm()

    # Chuẩn bị dữ liệu
    items, total = [], 0
    for pid, qty in cart.items():
        product    = get_object_or_404(Product, id=pid)
        line_total = product.price * qty
        items.append({
            'product':        product,
            'quantity':       qty,
            'price_vnd':      f"{int(product.price):,}".replace(',', '.') + " VND",
            'line_total_vnd': f"{int(line_total):,}".replace(',', '.') + " VND",
        })
        total += line_total

    total_vnd = f"{int(total):,}".replace(',', '.') + " VND"
    return render(request, 'shop/checkout.html', {
        'form':      form,
        'items':     items,
        'total_vnd': total_vnd,
    })

# Trang thành công
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})

# CRUD sản phẩm cho admin
@superuser_required
def admin_product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'shop/admin_product_list.html', {'products': products})

@superuser_required
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'shop/admin_product_form.html', {'form': form})

@superuser_required
def admin_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/admin_product_form.html', {
        'form':    form,
        'product': product,
    })

@superuser_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_product_list')
    return render(request, 'shop/admin_product_confirm_delete.html', {
        'product': product,
    })

# Lịch sử đơn hàng của user
@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related('product').all()
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'items': items,
    })
