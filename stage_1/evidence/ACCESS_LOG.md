# Access evidence — 2026-11-02

This is an audit log of observations, not a claim of downloading medical images.

| Check | Observed result |
| --- | --- |
| USC official database site | Browser service read page, data DOI and companion-code link. |
| USC author-hosted acquisition PDF | Browser service read 14-page paper, acquisition parameters and data formats. |
| USC Figshare landing/DOI | Browser service could not fetch redirected record. Dataset license unverified. |
| DVTD Springer Nature/Figshare record 11897187 | Browser service read public archive entry, 1.05 GB download and explicit CC0 license link. |
| DVTD methods paper | Browser service read MRI parameters, dental-cast methods, nasal exclusion and file descriptions. |
| HaN-Seg record 7442914 | Browser service read data description, archive size and MD5; license field lacked rendered value. |
| ToothFairy2 | Official indexed page supplied access/license/spacing statements; direct open returned 403. Organizer GitHub JSON supplied exact license identifier and labels. |
| Runtime urllib request: https://api.figshare.com/v2/articles/13725546 | Tunnel connection failed: 403 Forbidden. No metadata payload or scans saved. |
| Runtime urllib request: https://api.figshare.com/v2/articles/11897187 | Tunnel connection failed: 403 Forbidden. No metadata payload or scans saved. |
| Runtime urllib request: https://zenodo.org/api/records/7442914 | Tunnel connection failed: 403 Forbidden. No metadata payload or scans saved. |

Record-versus-file distinction: a visible download button proves a published retrieval route, not a completed transfer or usable volume. No DICOM headers, voxel arrays, cast geometry or anatomical segmentations were inspected. No archive checksum has been verified locally. No terms requiring registration were accepted.
