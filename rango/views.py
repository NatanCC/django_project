# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from rango.bing_search import run_query
from django.contrib.auth.models import User
from rango.models import UserProfile
from django.shortcuts import redirect

def index(request):

    context = RequestContext(request)

    category_list = get_category_list()
    context_dict = {'categories': category_list}
    try:
        top_pages = Page.objects.order_by('-views')[:5]
        context_dict['top_pages']=top_pages
    except Page.DoesNotExist:
        pass

    for category in category_list:
        category.url = category.name.replace(' ', '_')

    
    response = render_to_response('rango/index.html', context_dict, context)

    visits = int(request.COOKIES.get('visits', '0'))

    if 'last_visit' in request.COOKIES:

        last_visit = request.COOKIES['last_visit']

        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 5:

            response.set_cookie('visits', visits+1)

            response.set_cookie('last_visit', datetime.now())
    else:

        response.set_cookie('last_visit', datetime.now())

    return response

def category(request, category_name_url):

    context = RequestContext(request)
    
    context_dict = {'category_name_url': category_name_url}
    category_name = category_name_url.replace('_', ' ')

    context_dict['category_name'] = category_name

    try:
        category = Category.objects.get(name=category_name)

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages

        context_dict['category'] = category

    except Category.DoesNotExist:

        pass

    return render_to_response('rango/category.html',context_dict, context)

@login_required
def add_category(request):

    context = RequestContext(request)
    category_list = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)

            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    for i in category_list:
        print i.url
    return render_to_response('rango/add_category.html', {'form': form, 'categories': category_list}, context)

def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():

            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:

                return render_to_response('rango/add_category.html', {}, context)
            page.views = 0

            page.save()

            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()
    return render_to_response('rango/add_page.html',
            {'category_name_url': category_name_url,
            'category_name': category_name,
            'nao_e_post': "nao e  post",
            'form': form},
            context)
def decode_url(url_name):
    return url_name.replace('_', ' ')

def encode_url(name):
    return name.replace(' ', '_')
def register(request):
    if request.session.test_cookie_worked():
        print ">>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()

    context = RequestContext(request)

    registered = False

    if request.method == 'POST':

        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            registered = True
        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response(
            'rango/register.html',
            {'user_form':user_form,
            'profile_form':profile_form,
            'registered': registered},
            context)
def user_login(request):

    context = RequestContext(request)

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:

            if user.is_active:

                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:

                return HttpResponse('Your rango account is disabled')
        else:

            print 'Invalid login details: {0}, {1}'.format(username, password)
            return HttpResponse("Invalid Login details supplied")
    else:

        return render_to_response('rango/login.html', {}, context)

@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

def user_logout(request):

    logout(request)

    return HttpResponseRedirect('/rango/')

def search(request):
    context = RequestContext(request)
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:

            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list}, context)

def get_category_list():
    cat_list = Category.objects.all()

    for cat in cat_list:
        cat.url = encode_url(cat.name)

    return cat_list


@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'categories': cat_list}
    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
        print 'userprofile achado'
    except:
        up = None
        print 'nao tem userprofile'

    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views += 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)
