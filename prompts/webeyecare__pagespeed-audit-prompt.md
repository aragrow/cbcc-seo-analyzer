## About the Client

- The client is a developer maintaining a BigCommerce store.  
- They are seeking technical insights and practical SEO improvements.  
- Primary goals: increase rankings, improve visibility, enhance site speed, and optimize UX within the BigCommerce platform limitations.

Emphasize:

- Site speed optimization (especially mobile)  
- Structured data opportunities  
- Mobile usability and core web vitals  
- Crawlability and indexation  
- Content and metadata structure  
- Practical steps (theme, admin panel, CDN/app suggestions)

## Known BigCommerce Platform Limitations (Exclude These from Recommendations)

The following are known technical constraints of BigCommerce. Do not include them in your recommendations unless you offer a clear workaround or theme-level customization.

1. URL Structure  
   - Cannot fully remove `/products/` or `/categories/`.

2. Head Tag Control  
   - Limited global `<head>` editing; meta tag conflicts may arise.

3. JavaScript Rendering  
   - No server-side rendering; content in heavy JS apps may not be indexed.

4. Schema Markup  
   - Basic schema only (Product, Organization).  
   - FAQPage, BreadcrumbList, etc., require manual edits.

5. Pagination  
   - No built-in `rel="prev"` / `rel="next"`.  
   - Filtered URLs can cause duplicate content.

6. Redirects  
   - No regex or dynamic rules; manual or bulk-import only.

7. AMP  
   - Not supported natively.

8. Sitemap.xml  
   - Auto-generated, no custom inclusion/exclusion logic.

9. Image Format  
   - Uploaded images auto-convert to JPEG.  
   - No native WebP/AVIF unless via CDN or 3rd-party app.

Focus your analysis and recommendations on what can be controlled within the BigCommerce environment using:

- Storefront theme changes  
- Admin configuration  
- SEO apps or middleware  
- CDN-based solutions