# /workspace/shiftwise/contact/views.py

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import ContactForm


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract cleaned data
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            # Prepare email content
            subject = f"New Contact Enquiry from {name}"
            full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

            try:
                # Send email to site administrators
                send_mail(
                    subject,
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,  # From email
                    [
                        admin[1] for admin in settings.ADMINS
                    ],  # To emails (ensure ADMINS is set)
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
                return redirect("contact:contact")
            except Exception as e:
                messages.error(
                    request, f"An error occurred while sending your message: {str(e)}"
                )
    else:
        form = ContactForm()

    context = {"form": form}
    return render(request, "contact/contact.html", context)
