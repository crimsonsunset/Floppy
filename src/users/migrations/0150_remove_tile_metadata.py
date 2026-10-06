from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0149_merge_home_screen_and_cards"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="tile_metadata",
        ),
    ]
