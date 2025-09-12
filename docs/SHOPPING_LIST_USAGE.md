# Shopping List Management Feature

This document demonstrates how to use the new shopping list management feature that was implemented in response to the Portuguese healthy shopping list request.

## Overview

The shopping list feature integrates with the existing family budget control system to help families:
- Create monthly shopping lists with healthy food items
- Track estimated vs actual spending
- Monitor budget compliance
- Categorize items for better organization
- Include health benefits information for educational purposes

## Usage Examples

### 1. Create a Healthy Shopping List Template

```bash
# Create a comprehensive healthy shopping list for a family
python manage.py create_healthy_shopping_template \
    --family-budget-id=1 \
    --month="2024-09" \
    --title="Lista Saudável Setembro 2024"
```

This creates a shopping list with 30+ healthy items totaling approximately €95.80, including:
- Fresh fruits and vegetables (maçãs nacionais, brócolos, espinafres)
- Quality proteins (peito de frango bio, salmão fresco, ovos bio)
- Healthy dairy products (iogurte natural, queijo fresco)
- Whole grains (aveia integral, arroz integral, quinoa)
- Nutritious snacks (nozes, amêndoas, tâmaras)

### 2. Working with Shopping Lists in Code

```python
from finances.models import ShoppingList, ShoppingListItem, ShoppingCategory
from decimal import Decimal

# Get a shopping list
shopping_list = ShoppingList.objects.get(id=1)

# Check budget status
print(f"Budget remaining: €{shopping_list.budget_remaining}")
print(f"Over budget: {shopping_list.is_over_budget}")
print(f"Completion: {shopping_list.completion_percentage}%")

# Mark items as purchased
apples = shopping_list.items.get(name="Maçãs Nacionais")
apples.mark_purchased(Decimal("3.20"))  # Actual price paid

# Add custom items
ShoppingListItem.objects.create(
    shopping_list=shopping_list,
    name="Pão de Centeio",
    category=ShoppingCategory.GRAINS_CEREALS,
    quantity="1 unidade",
    estimated_price=Decimal("1.80"),
    health_benefits="Rico em fibra e vitaminas do complexo B"
)

# Update totals
shopping_list.update_totals()
```

### 3. Admin Interface Features

The admin interface provides:
- **Shopping List Management**: View all lists with completion status and budget tracking
- **Inline Item Editing**: Add/edit items directly within the shopping list
- **Bulk Actions**: Mark multiple items as purchased/skipped
- **Filtering & Search**: Find lists by family, month, completion status
- **Visual Indicators**: Color-coded budget status and completion progress

### 4. Categories and Health Benefits

Items are categorized into healthy food groups:
- 🥬 **Frutas e Vegetais**: Fresh fruits and vegetables
- 🥩 **Proteínas**: Lean meats, fish, legumes
- 🥛 **Lacticínios**: Dairy products
- 🌾 **Cereais e Grãos**: Whole grains and cereals
- 🥜 **Snacks Saudáveis**: Nuts and healthy snacks
- 🥤 **Bebidas**: Healthy beverages
- 🌿 **Ervas e Especiarias**: Herbs and spices
- 🍯 **Despensa Básica**: Pantry staples

Each item includes educational health benefits in Portuguese, helping families make informed nutrition choices.

## Integration with Budget Controls

Shopping lists automatically integrate with existing `FamilyBudgetControl` settings:
- Respects monthly and weekly budget limits
- Tracks spending against allocated budgets
- Provides warnings when approaching or exceeding limits
- Maintains audit trail of spending decisions

## Technical Details

### Models Created
- `ShoppingList`: Main shopping list entity linked to family budget control
- `ShoppingListItem`: Individual items with pricing, categories, and status
- `ShoppingCategory`: Enum for food categories
- `ShoppingItemStatus`: Enum for item status (pending/purchased/skipped)

### Database Fields
All models include proper validation, relationships, and Portuguese language support.

### Tests
Comprehensive test suite covers:
- Model creation and validation
- Business logic (totals calculation, completion percentage)
- Integration with budget controls
- Item status management

### Admin Interface  
Full-featured admin with:
- List views with sorting and filtering
- Inline editing for shopping list items
- Bulk actions for common operations
- Visual indicators for status and budget compliance

This implementation successfully addresses the original Portuguese request for a healthy shopping list by creating a comprehensive family budget-integrated shopping management system.