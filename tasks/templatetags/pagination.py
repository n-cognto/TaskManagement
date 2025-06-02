from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def paginate(context, page_obj, adjacent_pages=2):
    """
    Generates pagination controls with the specified number of adjacent pages.
    
    Usage:
    {% load pagination %}
    {% paginate page_obj 2 %}
    """
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    
    # If there are fewer than 2 pages, don't show pagination
    if total_pages <= 1:
        return ""
    
    page_range = []
    
    # Always include the first page
    page_range.append(1)
    
    # Calculate the range of page numbers to show
    start_page = max(2, current_page - adjacent_pages)
    end_page = min(total_pages - 1, current_page + adjacent_pages)
    
    # Add ellipsis after first page if needed
    if start_page > 2:
        page_range.append('...')
        
    # Add the calculated range
    page_range.extend(range(start_page, end_page + 1))
    
    # Add ellipsis before last page if needed
    if end_page < total_pages - 1:
        page_range.append('...')
        
    # Always include the last page
    if total_pages > 1:
        page_range.append(total_pages)
    
    # Generate HTML for pagination controls
    html = ['<nav aria-label="Page navigation"><ul class="pagination">']
    
    # Previous button
    if page_obj.has_previous():
        html.append(f'<li class="page-item"><a class="page-link" href="?page={page_obj.previous_page_number()}" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>')
    else:
        html.append('<li class="page-item disabled"><a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>')
    
    # Page numbers
    for page in page_range:
        if page == '...':
            html.append('<li class="page-item disabled"><span class="page-link">...</span></li>')
        elif page == current_page:
            html.append(f'<li class="page-item active"><span class="page-link">{page}<span class="sr-only">(current)</span></span></li>')
        else:
            html.append(f'<li class="page-item"><a class="page-link" href="?page={page}">{page}</a></li>')
    
    # Next button
    if page_obj.has_next():
        html.append(f'<li class="page-item"><a class="page-link" href="?page={page_obj.next_page_number()}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>')
    else:
        html.append('<li class="page-item disabled"><a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>')
    
    html.append('</ul></nav>')
    
    return mark_safe(''.join(html))