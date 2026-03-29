"""
This file looks at the URL when a rquest comes in and decides which app should handle it. (In our case it passes everything to the mining app's own URL)

"""

from django.urls import path, include

urlpatterns = [ 
    path('', include('mining.urls')),
]