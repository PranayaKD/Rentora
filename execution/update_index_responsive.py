with open('templates/index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace â‚¹ with ₹
content = content.replace('â‚¹', '₹')

# Replace Budget Section grid
content = content.replace(
    'class="cars-section grid md:grid-cols-2 lg:grid-cols-3 gap-12"',
    'class="cars-section grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8"'
)

# Replace Luxury Section grid & badge
content = content.replace(
    'class="cars-section grid md:grid-cols-3 gap-12"',
    'class="cars-section grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8"'
)
content = content.replace(
    'bg-accent text-primary text-[10px] font-bold uppercase tracking-widest mb-6 shadow-xl shadow-accent/20',
    'bg-accent text-white font-black text-[10px] uppercase tracking-widest mb-6 shadow-xl shadow-accent/20'
)

# Replace Electric section grid
content = content.replace(
    'class="grid md:grid-cols-2 lg:grid-cols-3 gap-8"',
    'class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8"'
)

# Replace max-w-7xl containers
content = content.replace(
    '<div class="max-w-7xl mx-auto px-6">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6">'
)
content = content.replace(
    '<div class="max-w-7xl mx-auto px-6 relative z-10">',
    '<div class="max-w-7xl 2xl:max-w-[1500px] mx-auto px-4 sm:px-6 relative z-10">'
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated index.html successfully')
