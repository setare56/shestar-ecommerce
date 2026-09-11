from django.db import migrations, models


def map_old_categories(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    mapping = {
        'tops': 'crops-tees',
        'shirts': 'dresses',
        'knitwear': 'crops-tees',
        'dresses': 'dresses',
        'sets': 'crops-tees',
        'bottoms': 'skirts-shorts',
        'outerwear': 'dresses',
        'shoes': 'bags-hats',
        'bags': 'bags-hats',
        'accessories': 'bags-hats',
    }
    for old, new in mapping.items():
        Product.objects.filter(category=old).update(category=new)


class Migration(migrations.Migration):
    dependencies = [('shop', '0002_real_store')]

    operations = [
        migrations.RunPython(map_old_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                choices=[
                    ('bags-hats', 'کیف و کلاه'),
                    ('dresses', 'پیراهن'),
                    ('skirts-shorts', 'شلوارک و دامن'),
                    ('crops-tees', 'کراپ و تیشرت'),
                ],
                max_length=20,
                verbose_name='دسته بندی',
            ),
        ),
    ]
