from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request,'index.html')

def featured_books(request):
    return render(request,'featured_books.html')

def popular(request):
    return render(request,'popular.html')

def offers(request):
    return render(request,'offers.html')

def articles(request):
    return render(request,'articles.html')
