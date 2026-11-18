with open('templates/cars.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace â‚¹ with ₹
content = content.replace('â‚¹', '₹')
content = content.replace('â€¢', '•')
content = content.replace('â†’', '→')
content = content.replace('â˜…', '★')

# Update max-w-7xl in cars.html
content = content.replace(
    '<div class="max-w-7xl mx-auto flex items-center justify-between gap-3">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto flex items-center justify-between gap-3">'
)
content = content.replace(
    '<div id="quick-filter-pills" class="max-w-7xl mx-auto mt-3 flex items-center',
    '<div id="quick-filter-pills" class="max-w-7xl 2xl:max-w-[1500px] mx-auto mt-3 flex items-center'
)
content = content.replace(
    '<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 pb-36 md:py-6 flex flex-col md:flex-row gap-8 items-start">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6 pt-4 pb-36 md:py-6 flex flex-col md:flex-row gap-6 lg:gap-8 items-start">'
)
content = content.replace(
    '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-4 gap-4" id="cars-grid">',
    '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6" id="cars-grid">'
)

with open('templates/cars.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated cars.html successfully')
