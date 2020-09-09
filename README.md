# some_site_analysis_tools
Short scripts to check some aspects of a web app

xml sitemap checker: 
one-file cli tool that accepts an xml sitemap link, goes through its urls 
and outputs the obtained responses and errors. 
Can can create a txt file in the same folder and write there all sitemap urls with their responses

website pages checker for broken links:
one-file cli tool that accepts a website url and tries to go through all revealed internal pages
the main purpose is to detect links with non-200 responses, since they worsen the seo
also finds double urls
generally, this program is my take on composition in Python

