with open('templates/car-detail.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace â‚¹ with ₹
content = content.replace('â‚¹', '₹')
content = content.replace('â€¢', '•')
content = content.replace('â†’', '→')
content = content.replace('ðŸ“ ', '📍 ')

# Update max-w-7xl
content = content.replace(
    '<div class="max-w-7xl mx-auto flex items-center justify-between">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto flex items-center justify-between">'
)
content = content.replace(
    '<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-28 lg:pb-12">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6 py-6 pb-28 lg:pb-12">'
)

# Scale gallery image container
content = content.replace(
    '<div class="w-full max-w-xl h-56 sm:h-72 flex items-center justify-center py-2 relative group">',
    '<div class="w-full max-w-xl lg:max-w-2xl xl:max-w-3xl h-56 sm:h-72 md:h-80 lg:h-96 xl:h-[420px] flex items-center justify-center py-2 relative group">'
)

with open('templates/car-detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated car-detail.html successfully')
