# /workspace/shiftwise/home/views.py

from django.views.generic import TemplateView

from subscriptions.models import Plan


class HomeView(TemplateView):
    """
    Home view for the application, displaying subscription plans.
    Accessible to all users.
    """

    template_name = "home/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch all active subscription plans
        plans = Plan.objects.filter(is_active=True).order_by("name", "billing_cycle")
        
        # Group plans by name
        plan_dict = {}
        for plan in plans:
            if plan.name not in plan_dict:
                plan_dict[plan.name] = {
                    "name": plan.name,
                    "description": plan.description,
                    "custom_integrations": plan.custom_integrations,
                    "monthly_plan": None,
                    "yearly_plan": None,
                }
            if plan.billing_cycle.lower() == "monthly":
                plan_dict[plan.name]["monthly_plan"] = plan
            elif plan.billing_cycle.lower() == "yearly":
                plan_dict[plan.name]["yearly_plan"] = plan
        
        # Convert plan_dict to a list for easy iteration in templates
        available_plans = list(plan_dict.values())
        
        context["available_plans"] = available_plans
        return context