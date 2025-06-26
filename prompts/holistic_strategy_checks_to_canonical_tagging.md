##Holistic Strategy Checks to Canonical Tagging

Perform These checks ensure the overall strategy is consistent and logical.
### Check 1: The Canonical URL's HTTP Status Code
The destination of your canonical tag must return a 200 OK status code.
#### How to Check: Crawl the canonical URL from each pair and verify its status code.
 #### Red Flags:
Pointing to a 301 Redirect: This creates an unnecessary chain. While Google can often follow it, it's inefficient and bad practice. The canonical should be the final destination.
Pointing to a 404 (Not Found): This is a major error. You are telling Google the master version of this page doesn't exist. The signal will likely be ignored, and you'll get no SEO benefit.
Pointing to a 5xx (Server Error): Also a major error. This signals to Google that your main page is broken.
### Check 2: The Canonical URL's Indexability
The destination of your canonical tag must be indexable.
#### How to Check:
Check the robots meta tag on the canonical URL's page. It must NOT contain noindex.
Check your website's robots.txt file. The canonical URL must NOT be disallowed.
#### Red Flags: Pointing to a non-indexable page sends a completely contradictory signal to Google: "This is the master page, but please don't index it." Google will likely get confused and may choose to index the wrong page or neither.
### Check 3: The Master Page Must Be Self-Referencing
The page you consider the "master" version must have a canonical tag that points to itself.
#### How to Check: For the URL that is the clean, master version (e.g., https://webeyecare.com/acuvue-oasys-for-astigmatism-6-pack), its own canonical tag must also be https://webeyecare.com/acuvue-oasys-for-astigmatism-6-pack.
#### Red Flags: If your master page points to a different URL, you are giving away its authority and creating a potential canonical chain.
### Check 4: Use Absolute, Not Relative, URLs
The href attribute of your canonical tag must be an absolute URL.
#### How to Check: Ensure every canonical URL in your array starts with https:// (or http://).
#### Red Flags: Using a relative URL like /acuvue-oasys-for-astigmatism-6-pack or acuvue-oasys-for-astigmatism-6-pack.html. This can be misinterpreted by crawlers and lead to errors, especially on sites with complex structures or subdomains.
Wrong: <link rel="canonical" href="/acuvue-oasys-for-astigmatism-6-pack">
Right: <link rel="canonical" href="https://webeyecare.com/acuvue-oasys-for-astigmatism-6-pack">
### Check 5: Content Similarity
The content of the url and its canonical should be the same or nearly identical.
#### How to Check: This is a manual check. Is the page with ?color=blue showing the same product as the clean URL, just with a different color pre-selected? If so, that's perfect.
#### Red Flags: If the content is significantly different, Google may learn to ignore your canonical tag as an untrustworthy signal. Don't try to use canonicals to pass authority between completely unrelated pages.
### Check 6: All Duplicates Point to a Single Master
All variations of a page must point to the exact same canonical URL.
#### How to Check: Filter your array for all URLs related to a single page (e.g., all variations of /acuvue-oasys-for-astigmatism-6-pack). Verify that the canonical value is identical for all of them.
#### Red Flags:
.../acuvue-oasys-for-astigmatism-6-pack?color=blue points to https://webeyecare.com/acuvue-oasys-for-astigmatism-6-pack
.../acuvue-oasys-for-astigmatism-6-pack?sort=price points to https://webeyecare.com/acuvue-oasys-for-astigmatism-6-pack/ (with a trailing slash)
This "scatters" the authority instead of consolidating it.
### Check 7: No Canonical Chains
A page should never point to another page that itself has a different canonical tag.
#### How to Check: For a pair (A, B), look up the pair for B, which might be (B, C). If B is not the same as C, you have a chain A -> B -> C.
#### Red Flags: A canonical chain. The correct implementation is for both A and B to point directly to C.
### Check 8: Check for Mixed Signals
The canonical tag is just one signal. You need to ensure other signals don't contradict it.
#### How to Check:
Sitemaps: Your XML sitemap should only contain the canonical URLs. Never include non-canonical (parameterized, etc.) URLs.
Internal Links: Wherever possible, your internal links should point directly to the canonical URL. It's not a critical error to link to a non-canonical version, but it's cleaner to link to the master page.
Hreflang Tags: If you use hreflang for international versions, the URLs listed there must also be the canonical versions for each language.
