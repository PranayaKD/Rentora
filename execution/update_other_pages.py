templates_to_update = [
    'templates/payment.html',
    'templates/how-it-works.html',
    'templates/why-rentora.html',
    'templates/airport-transfer.html',
    'templates/subscription.html',
    'templates/components/footer.html'
]

for t in templates_to_update:
    try:
        with open(t, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Fix common mojibake
        content = content.replace('â‚¹', '₹')
        content = content.replace('â€¢', '•')
        content = content.replace('â†’', '→')
        content = content.replace('â˜…', '★')

        # Update max-w-7xl to responsive 2xl:max-w-[1500px]
        content = content.replace(
            '<div class="max-w-7xl mx-auto px-4 sm:px-6">',
            '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6">'
        )
        content = content.replace(
            '<div class="max-w-7xl mx-auto px-6">',
            '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6">'
        )
        content = content.replace(
            '<div class="max-w-7xl mx-auto px-6 flex items-center justify-between">',
            '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6 flex items-center justify-between">'
        )
        content = content.replace(
            '<div class="max-w-7xl mx-auto px-6 py-10">',
            '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6 py-10">'
        )

        with open(t, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {t}')
    except Exception as e:
        print(f'Error updating {t}: {e}')
