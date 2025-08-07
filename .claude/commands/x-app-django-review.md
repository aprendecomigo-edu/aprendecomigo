Your task is to verify the health of the project and apply best practices for dealing with cross-dependencies in Django apps:

1. Use lazy references ("app.Model" strings or settings.AUTH_USER_MODEL) for compile-time relationships.
2. Use the app-registry (apps.get_model() or AppConfig.ready()) for runtime wiring such as signals, admin registration, or feature flags.
3. Declare migration dependencies explicitly—and conditionally—when automatic inference is not enough.
4. If two apps constantly talk to each other, reconsider your boundaries or introduce an interface layer instead of direct imports.

This is a complex task so plan well and use sequential thinking.

## 1. Keep model-level links lazy
ForeignKey, ManyToMany & OneToOne
Define relationships with a string reference, example:

```python
class Order(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT)
```
Because Django resolves the string after every app’s models module is imported, you avoid circular imports in 99 % of cases — and migrations will add the correct dependency automatically 

AUTH_USER_MODEL and other settings-based indirection
For global references, use the dotted-path stored in settings (settings.AUTH_USER_MODEL, your own MYAPP_SHOPPER_MODEL, etc.). These are resolved lazily through the same mechanism 


## 2. Runtime wiring via the App Registry
`apps.get_model()`
When you genuinely need the class at runtime (inside a signal handler, a utility function, a Celery task…), fetch it from the registry instead of importing at module top-level, example:
```python
from django.apps import apps

def latest_invoice_for(customer_id):
    Invoice = apps.get_model("billing", "Invoice")
    return Invoice.objects.filter(customer_id=customer_id).latest("pk")

```
require_ready=True (default) guarantees the model is fully initialised
AppConfig.ready() for once-per-process hooks
Put cross-app initialisation here—admin registrations, checks, or signal connections:
```python
class BillingConfig(AppConfig):
    name = "billing"

    def ready(self):
        from django.db.models.signals import post_save
        Customer = self.get_model("Customer")          # safe here
        from billing.signals import issue_welcome_coupon
        post_save.connect(issue_welcome_coupon, sender=Customer)

```
ready() runs after the registry is populated, so you avoid AppRegistryNotReady errors
Tip: guard with a module-level flag if the code could run twice under the Django test runner.

## 3. Managing migration dependencies
Let Django infer, but override when needed
Django builds a graph; string relations usually suffice. If inference fails (or if you add data migrations that touch another app), add manual edges:
```python
class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0007_recalculate_stock_levels"),
        ("orders", "0012_auto"),
    ]
```
Automatic scheduling improved again in 5.2, but circular graphs can still bite.

Conditional / optional apps
When an app is optional, wrap access in try/except LookupError and compute dependencies dynamically:
```python
from django.apps import apps
from django.db import migrations

optional = []
if apps.is_installed("tags"):
    optional.append(("tags", "0003_initial"))

class Migration(migrations.Migration):
    dependencies = [("blog", "0005_slug_immutable"), *optional]
```
This pattern—discussed on the Django Forum—prevents crashes when the optional app isn’t installed 

## 5. Taming circular imports in plain Python code
- Import inside functions or methods rather than at module top-level.
- Split large modules: move business logic to services.py, leaving models lean.
- If both apps need something common, extract it into a third “library” app

## 6. When boundaries feel wrong—re-draw them
If you need many ForeignKeys in both directions, Admin in one app referring heavily to Models in another, or migrations depend on each other every release, you may have an artificial split. Collapsing the two apps (or introducing a thin interface layer) often simplifies everything

## 7. Checklist to review before you hit commit
1.String-based relations only?
2. No top-level imports of sibling app models or tasks?
4. Migrations have explicit or conditional dependencies when needed?
5. Unit tests cover the “app missing” scenario if the dependency is optional?