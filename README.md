# geo-scraping
Scraping open source geospatial data resources for satellite imagery and vector labeling. 

Long-term goal to create benchmark dataset consisting of high-resolution satellite imagery with hierarchical labels on the scale of ImageNet!

---

## Documents
[Overview in Google Drive](https://docs.google.com/document/d/1LZF6pNe4lkTXCMtIQ-QEX1oLKchhDIapM7k9Mr_Q3fY/edit#heading=h.i0ctbfaedsq)


## Tasks

### Catalog largest Highres Datasets
OSM can provide vector labels, but a global uniform image dataset does not exist at resolutions higher than 30m/px.

### Extract classes cleanly from OSM
Need to create a pipeline to take a Lat/Lon bounding box and export all the contained classes as so:
- Building footprint polygons with osm metadata
- Road Polylines, minimizing repeats.
- All OSM verified classes in bounds
