# -*- coding: utf-8 -*-

u"""
.. module:: organizations
"""

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.text import slugify
from django.views.generic import View

from volontulo.forms import VolounteerToOrganizationContactForm
from volontulo.lib.email import send_mail
from volontulo.models import Offer
from volontulo.models import Organization
from volontulo.models import UserProfile
from volontulo.utils import correct_slug
from volontulo.views import yield_message_error_form
from volontulo.views import yield_message_successful_email


def organizations_list(request):
    u"""View responsible for listing all organizations."""
    organizations = Organization.objects.all()
    return render(
        request,
        "organizations/list.html",
        {'organizations': organizations},
    )


class OrganizationsCreate(View):
    u"""Class view supporting creation of new organization."""

    @staticmethod
    def get(request):
        u"""Method responsible for rendering form for new organization."""
        return render(
            request,
            "organizations/organization_form.html",
            {'organization': Organization()}
        )

    @staticmethod
    def post(request):
        u"""Method resposible for saving new organization."""
        organization = Organization(
            name=request.POST.get('name'),
            address=request.POST.get('address'),
            description=request.POST.get('description'),
        )
        organization.save()
        request.user.userprofile.organizations.add(organization)
        return redirect(
            'organization_view',
            slug=slugify(organization.name),
            id_=organization.id,
        )


@correct_slug(Organization, 'organization_form', 'name')
# pylint: disable=unused-argument
def organization_form(request, slug, id_):
    u"""View responsible for editing organization.

    Edition will only work, if logged user has been registered as organization.
    """
    org = Organization.objects.get(pk=id_)
    if not (
            request.user.is_authenticated() and
            UserProfile.objects.get(user=request.user).organizations
    ):
        return redirect('homepage')

    if request.method == 'POST':
        org.name = request.POST.get('name')
        org.address = request.POST.get('address')
        org.description = request.POST.get('description')
        org.save()
        return redirect(
            reverse(
                'organization_view',
                args=[slugify(org.name), org.id]
            )
        )

    return render(
        request,
        "organizations/organization_form.html",
        {'organization': org},
    )


@correct_slug(Organization, 'organization_view', 'name')
# pylint: disable=unused-argument
def organization_view(request, slug, id_):
    u"""View responsible for viewing organization."""
    org = get_object_or_404(Organization, id=id_)

    offers = Offer.objects.filter(organization_id=id_)
    if request.method == 'POST':
        form = VolounteerToOrganizationContactForm(request.POST)
        if form.is_valid():
            profile = UserProfile.objects.get(organization_id=id_)
            send_mail(
                'volunteer_to_organisation',
                [
                    profile.user.email,
                    request.POST.get('email'),
                ],
                {k: v for k, v in request.POST.items()},
            )
            yield_message_successful_email(request)
        else:
            yield_message_error_form(request, form)
            return render(
                request,
                "organizations/organization_view.html",
                {
                    'organization': org,
                    'contact_form': form,
                    'offers': offers,
                },
            )
    form = VolounteerToOrganizationContactForm()
    return render(
        request,
        "organizations/organization_view.html",
        {
            'organization': org,
            'contact_form': form,
            'offers': offers,
        },
    )
