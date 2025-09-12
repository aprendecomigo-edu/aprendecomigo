"""
Management command to create healthy shopping list templates.

This command creates a comprehensive healthy shopping list template based on 
Portuguese healthy eating guidelines, inspired by the Continente.pt request.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finances.models import ShoppingCategory, ShoppingList, ShoppingListItem


class Command(BaseCommand):
    help = "Create healthy shopping list templates for Portuguese families"

    def add_arguments(self, parser):
        parser.add_argument(
            "--family-budget-id",
            type=int,
            help="ID of the FamilyBudgetControl to create shopping list for",
        )
        parser.add_argument(
            "--month",
            type=str,
            default=date.today().strftime("%Y-%m"),
            help="Month for the shopping list (YYYY-MM format, default: current month)",
        )
        parser.add_argument(
            "--title",
            type=str,
            default="Lista de Compras Saudáveis - {month}",
            help="Title for the shopping list",
        )

    def handle(self, *args, **options):
        family_budget_id = options.get("family_budget_id")
        month_str = options["month"]
        title_template = options["title"]

        if not family_budget_id:
            raise CommandError("--family-budget-id is required")

        # Validate and parse month
        try:
            month_date = date.fromisoformat(f"{month_str}-01")
        except ValueError:
            raise CommandError(f"Invalid month format: {month_str}. Use YYYY-MM format.")

        # Import here to avoid circular imports
        from finances.models import FamilyBudgetControl

        try:
            family_budget = FamilyBudgetControl.objects.get(id=family_budget_id)
        except FamilyBudgetControl.DoesNotExist:
            raise CommandError(f"FamilyBudgetControl with id {family_budget_id} does not exist")

        title = title_template.format(month=month_date.strftime("%B %Y"))

        self.stdout.write(f"Creating healthy shopping list for {family_budget}...")
        self.stdout.write(f"Month: {month_date.strftime('%B %Y')}")
        self.stdout.write(f"Title: {title}")

        with transaction.atomic():
            # Create or get the shopping list
            shopping_list, created = ShoppingList.objects.get_or_create(
                family_budget_control=family_budget,
                month_year=month_date,
                defaults={
                    "title": title,
                    "notes": "Lista de compras saudáveis baseada em diretrizes nutricionais portuguesas. "
                             "Prioriza alimentos frescos, locais e nutritivos para uma alimentação equilibrada.",
                }
            )

            if not created:
                self.stdout.write(
                    self.style.WARNING(f"Shopping list already exists for {month_date.strftime('%B %Y')}")
                )
                return

            # Generate healthy shopping items
            healthy_items = self._get_healthy_items_template()
            
            total_items = 0
            total_estimated_cost = Decimal("0.00")

            for category, items in healthy_items.items():
                for item_data in items:
                    item = ShoppingListItem.objects.create(
                        shopping_list=shopping_list,
                        name=item_data["name"],
                        category=category,
                        quantity=item_data["quantity"],
                        estimated_price=Decimal(str(item_data["estimated_price"])),
                        health_benefits=item_data["health_benefits"],
                        notes=item_data.get("notes", ""),
                        order=item_data["order"],
                    )
                    total_items += 1
                    total_estimated_cost += item.estimated_price

            # Update shopping list totals
            shopping_list.estimated_total = total_estimated_cost
            shopping_list.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created shopping list '{title}' with {total_items} healthy items. "
                    f"Estimated total: €{total_estimated_cost}"
                )
            )

    def _get_healthy_items_template(self) -> Dict[str, List[Dict]]:
        """
        Generate a comprehensive healthy shopping list template.
        
        Based on Portuguese dietary guidelines and typical prices at major supermarkets
        like Continente. Focuses on fresh, seasonal, and nutritious foods.
        """
        return {
            ShoppingCategory.FRUITS_VEGETABLES: [
                {
                    "name": "Maçãs Nacionais",
                    "quantity": "2 kg",
                    "estimated_price": 3.50,
                    "health_benefits": "Rica em fibra, vitaminas C e antioxidantes. Ajuda na digestão e saúde cardiovascular.",
                    "notes": "Preferir maçãs da época e nacionais",
                    "order": 1,
                },
                {
                    "name": "Bananas",
                    "quantity": "1.5 kg",
                    "estimated_price": 2.25,
                    "health_benefits": "Rica em potássio, vitamina B6 e fibra. Excelente fonte de energia natural.",
                    "order": 2,
                },
                {
                    "name": "Laranjas",
                    "quantity": "2 kg", 
                    "estimated_price": 2.80,
                    "health_benefits": "Rica em vitamina C, folato e fibra. Fortalece o sistema imunitário.",
                    "order": 3,
                },
                {
                    "name": "Brócolos",
                    "quantity": "1 kg",
                    "estimated_price": 2.95,
                    "health_benefits": "Rico em vitamina K, C e ácido fólico. Propriedades anticancerígenas.",
                    "order": 4,
                },
                {
                    "name": "Espinafres Frescos",
                    "quantity": "500g",
                    "estimated_price": 1.75,
                    "health_benefits": "Rico em ferro, ácido fólico e vitamina K. Essencial para a saúde do sangue.",
                    "order": 5,
                },
                {
                    "name": "Cenouras",
                    "quantity": "1 kg",
                    "estimated_price": 1.20,
                    "health_benefits": "Rica em beta-caroteno (vitamina A), fibra e potássio. Boa para a visão.",
                    "order": 6,
                },
                {
                    "name": "Tomates Cherry",
                    "quantity": "500g",
                    "estimated_price": 2.50,
                    "health_benefits": "Rico em licopeno, vitamina C e potássio. Propriedades antioxidantes.",
                    "order": 7,
                },
                {
                    "name": "Cebolas",
                    "quantity": "1 kg",
                    "estimated_price": 1.10,
                    "health_benefits": "Rica em vitamina C e compostos sulfurosos. Anti-inflamatória natural.",
                    "order": 8,
                },
            ],
            
            ShoppingCategory.PROTEINS: [
                {
                    "name": "Peito de Frango Bio",
                    "quantity": "1 kg",
                    "estimated_price": 8.50,
                    "health_benefits": "Proteína magra de alta qualidade. Rica em vitaminas B e selénio.",
                    "notes": "Preferir de origem biológica",
                    "order": 10,
                },
                {
                    "name": "Salmão Fresco",
                    "quantity": "500g",
                    "estimated_price": 12.00,
                    "health_benefits": "Rico em ómega-3, proteína e vitamina D. Excelente para saúde cardiovascular.",
                    "order": 11,
                },
                {
                    "name": "Ovos Bio (Galinhas Criadas ao Ar Livre)",
                    "quantity": "1 dúzia",
                    "estimated_price": 3.20,
                    "health_benefits": "Proteína completa, colina e vitaminas B. Essencial para desenvolvimento cerebral.",
                    "order": 12,
                },
                {
                    "name": "Lentilhas Secas",
                    "quantity": "500g",
                    "estimated_price": 2.10,
                    "health_benefits": "Rica em proteína vegetal, fibra e ferro. Excelente alternativa à carne.",
                    "order": 13,
                },
                {
                    "name": "Grão-de-Bico",
                    "quantity": "500g",
                    "estimated_price": 1.80,
                    "health_benefits": "Rico em proteína, fibra e ácido fólico. Ajuda a controlar o colesterol.",
                    "order": 14,
                },
            ],
            
            ShoppingCategory.DAIRY: [
                {
                    "name": "Iogurte Natural sem Açúcar",
                    "quantity": "4 unidades",
                    "estimated_price": 3.60,
                    "health_benefits": "Rica em probióticos, cálcio e proteína. Melhora a saúde digestiva.",
                    "notes": "Escolher sem açúcares adicionados",
                    "order": 20,
                },
                {
                    "name": "Queijo Fresco",
                    "quantity": "200g",
                    "estimated_price": 2.40,
                    "health_benefits": "Rico em cálcio, proteína e vitamina B12. Baixo teor de gordura.",
                    "order": 21,
                },
                {
                    "name": "Leite Meio-Gordo",
                    "quantity": "1 litro",
                    "estimated_price": 1.20,
                    "health_benefits": "Rico em cálcio, vitamina D e proteína. Essencial para ossos fortes.",
                    "order": 22,
                },
            ],
            
            ShoppingCategory.GRAINS_CEREALS: [
                {
                    "name": "Aveia Integral",
                    "quantity": "500g",
                    "estimated_price": 2.30,
                    "health_benefits": "Rica em fibra solúvel, proteína e vitaminas B. Ajuda a controlar o colesterol.",
                    "order": 30,
                },
                {
                    "name": "Arroz Integral",
                    "quantity": "1 kg",
                    "estimated_price": 2.85,
                    "health_benefits": "Rico em fibra, vitaminas B e minerais. Melhor opção que arroz branco.",
                    "order": 31,
                },
                {
                    "name": "Quinoa",
                    "quantity": "500g",
                    "estimated_price": 4.50,
                    "health_benefits": "Proteína completa, rica em fibra e minerais. Super-alimento nutritivo.",
                    "order": 32,
                },
                {
                    "name": "Pão Integral de Centeio",
                    "quantity": "1 unidade",
                    "estimated_price": 1.90,
                    "health_benefits": "Rico em fibra, vitaminas B e minerais. Melhor digestão que pão branco.",
                    "order": 33,
                },
            ],
            
            ShoppingCategory.HEALTHY_SNACKS: [
                {
                    "name": "Nozes",
                    "quantity": "200g",
                    "estimated_price": 3.80,
                    "health_benefits": "Rica em ómega-3, proteína e vitamina E. Excelente para saúde cerebral.",
                    "order": 40,
                },
                {
                    "name": "Amêndoas",
                    "quantity": "200g",
                    "estimated_price": 4.20,
                    "health_benefits": "Rica em vitamina E, magnésio e fibra. Boa para saúde cardiovascular.",
                    "order": 41,
                },
                {
                    "name": "Tâmaras Secas",
                    "quantity": "250g",
                    "estimated_price": 3.10,
                    "health_benefits": "Rica em fibra, potássio e antioxidantes. Adoçante natural saudável.",
                    "order": 42,
                },
            ],
            
            ShoppingCategory.BEVERAGES: [
                {
                    "name": "Chá Verde",
                    "quantity": "20 saquetas",
                    "estimated_price": 2.50,
                    "health_benefits": "Rico em antioxidantes, catequinas. Propriedades anti-inflamatórias.",
                    "order": 50,
                },
                {
                    "name": "Água Mineral Natural",
                    "quantity": "6 garrafas 1.5L",
                    "estimated_price": 3.90,
                    "health_benefits": "Hidratação essencial. Rico em minerais naturais.",
                    "order": 51,
                },
            ],
            
            ShoppingCategory.HERBS_SPICES: [
                {
                    "name": "Azeite Extra Virgem",
                    "quantity": "500ml",
                    "estimated_price": 4.80,
                    "health_benefits": "Rico em antioxidantes e gorduras saudáveis. Anti-inflamatório natural.",
                    "notes": "Preferir azeite português de primeira pressão",
                    "order": 60,
                },
                {
                    "name": "Alho Fresco",
                    "quantity": "1 cabeça",
                    "estimated_price": 0.50,
                    "health_benefits": "Rico em compostos sulfurosos. Propriedades antibacterianas e antifúngicas.",
                    "order": 61,
                },
                {
                    "name": "Gengibre Fresco",
                    "quantity": "100g",
                    "estimated_price": 1.20,
                    "health_benefits": "Propriedades anti-inflamatórias e digestivas. Rico em gingerol.",
                    "order": 62,
                },
            ],
            
            ShoppingCategory.PANTRY_STAPLES: [
                {
                    "name": "Mel Puro",
                    "quantity": "250g",
                    "estimated_price": 4.50,
                    "health_benefits": "Adoçante natural com propriedades antibacterianas e antioxidantes.",
                    "notes": "Preferir mel nacional e não processado",
                    "order": 70,
                },
                {
                    "name": "Vinagre de Maçã",
                    "quantity": "500ml",
                    "estimated_price": 2.90,
                    "health_benefits": "Pode ajudar no controlo da glicemia e digestão. Rico em ácido acético.",
                    "order": 71,
                },
            ],
        }