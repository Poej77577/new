# Stage 1 — anatomical data and reconstruction feasibility

Audit date: 2026-11-02. **Stage 1 only; no segmentation, reconstruction, sculpting or rigging performed.** Existing `vocal_tract/` files are legacy synthetic models and are not medical-image-derived evidence. No anatomical illustration is present in the conversation attachments available for this audit.

## Decision

**Recommend Dresden Vocal Tract Dataset (DVTD) as the first acquisition/inspection candidate**, because the official archive explicitly carries CC0 and includes volumetric MRI plus dental casts from the same participants. This is a conditional starting point, not a claim that it can supply every required organ. Subject 1, sustained schwa (`s1-22-ehe-schwa`), is a reasonable inspection candidate; this is not a resting scan or an image-quality-approved selection.

USC 75-speaker MRI is the preferred alternative for resting soft-tissue anatomy plus speech movement references, pending dataset-level license confirmation and file access. Neither collection's pixel data was downloaded or inspected here. A complete anatomically verified asset is **not yet demonstrated feasible**; an image-backed partial reconstruction is plausible.

## Candidate comparison and verified rights

| Source | Proposed role | Access/rights evidence | Decision |
| --- | --- | --- | --- |
| [DVTD official archive](https://springernature.figshare.com/articles/dataset/Dresden_Vocal_Tract_Dataset_complete_archive_/11897187), DOI 10.6084/m9.figshare.11897187 | First volumetric MRI/dental candidate | Public landing page and 1.05 GB download entry observed. Dataset license explicitly **CC0**. Binary transfer not tested; runtime API requests blocked by proxy. | Selected for acquisition/inspection, subject to coverage and quality checks. |
| [USC 75-speaker MRI](https://sail.usc.edu/span/75speakers/), DOI 10.6084/m9.figshare.13725546.v1 | Rest anatomy, sustained 3D shapes and dynamic speech reference | Official site and paper verified. Exact Figshare dataset license could not be read. Author's public-domain wording specifically mentions raw RT-MRI; it must not be generalized to every file. | Conditional alternative; no clearance asserted for redistributing T2w/3D derivatives. |
| [ToothFairy2 official dataset information](https://toothfairy2.grand-challenge.org/dataset/) and [organizer metadata](https://github.com/AImageLab-zip/ToothFairy2-Benchmark/blob/main/dataset.json) | Supplementary CBCT bone/teeth morphology | Official indexed dataset page: registration required, CC BY-SA. Organizer JSON specifies **CC BY-SA 4.0**. Challenge description also includes research-purpose language. | Reserve only. Resolve actual download terms before use/distribution. It is not paired with the selected speech MRI subject. |
| [HaN-Seg](https://zenodo.org/records/7442914), DOI 10.5281/zenodo.7442914 | Investigated paired CT/MR option | Official record verifies 42 patients, 30 CT OAR masks, 4.9 GB archive. License field did not render in the accessed page. NIH catalog search metadata reports **CC BY-NC-ND 4.0**, not independently confirmed from the record API. | Excluded from this public derivative-asset route until authoritative rights clarification. Cancer anatomy and OAR masks are also not a normal complete vocal-tract atlas. |

[CC0 terms](https://creativecommons.org/publicdomain/zero/1.0/) allow copying, adaptation and distribution, including commercial use, subject to rights outside the waiver. Preserve scholarly attribution even where CC0 does not require it. The DVTD **dataset's CC0** is distinct from its paper's **CC BY 4.0**. The USC paper's CC BY and software's MIT licenses do not establish the dataset's license. No purchases, registration, data-use acceptance or messages to dataset owners were made.

## Anatomical reference findings

[DVTD methods and data records](https://pmc.ncbi.nlm.nih.gov/articles/PMC7406497/): two speakers, 22 sustained sounds each; MRI acquisition resolution **1.2 × 1.2 × 1.8 mm**, 44 slices. MRI is delivered as `.ima`; dental impressions were scanned into STL. These represent dental casts, not complete craniofacial bones, tooth roots or internal bone tissue. Published airway surfaces exclude the nasal cavity and describe oral/pharyngeal lumen boundaries, not separate tongue or velum solids. Files termed printable models include constructed wall thickness; they must not become anatomical tissue ground truth. Resampling to 0.25 mm in the published processing does not improve acquired anatomical resolution.

[USC acquisition paper](https://sail.usc.edu/publications/files/Lim_et_al-2021-Scientific_Data.pdf): 75 speakers; sustained volumes **1.5625 mm isotropic**, reconstructed MAT files; resting T2w **0.5859 mm in-plane, 3 mm slices**, DICOM stacks in several orientations. RT-MRI has **2.4 mm in-plane, 6 mm slice thickness**, about 83 frames/s; it is motion reference, not a full 3D anatomy reconstruction. Whole-release size is approximately 966 GB, so obtain only one participant's useful reconstructed files initially. Resting and phonating acquisitions need their own registration/pose handling.

[ToothFairy2 dataset page](https://toothfairy2.grand-challenge.org/dataset/) reports **0.3 mm isotropic** CBCT. The organizer label map distinguishes jaws and individual teeth. It is an additional donor population; fitting such structures to speech MRI creates a documented multi-donor composite, not a same-person reconstruction.

## Structure-by-structure feasibility — not segmentation results

| Required structure | Evidence-supported approach | Uncertainty to resolve on actual images |
| --- | --- | --- |
| Tongue | Volumetric MRI with manually reviewed boundaries | Deep/root interface, partial volume and tongue/floor separation; no complete tongue labels verified. |
| Soft palate / velum | MRI boundaries across adjacent planes | Thin free edge and uvula may be subvoxel; contact can merge tissue interfaces. |
| Nasal cavity / pharynx | Segment airspace and tissue walls separately from MRI | Nasal coverage, turbinate detail and air/bone ambiguity. DVTD's ready-made airway mesh omits nasal space. |
| Hard palate | MRI soft-tissue boundary; bone detail requires complementary evidence | MRI signal void does not establish cortical bone thickness. |
| Teeth | Same-participant DVTD dental cast surfaces preferred | Casts do not supply roots or internal dental anatomy. Registration/transforms must be verified. |
| Upper/lower jaws | CT/CBCT when licensed and adequately covered | Dental-cast filenames do not establish complete jaw geometry. Cross-donor fitting requires explicit provenance. |
| Lips / surrounding tissues | MRI if scan coverage and contrast permit | Small folds and layers can require later reference-guided manual work, marked as reconstruction. |

These are technical expectations, not observations of a selected scan. An airway mask does not define the complete tongue, lip or velum volume. No external illustration has yet been supplied for secondary visual comparison.

## Concrete next-stage gate

After user approval, first acquire one DVTD case, archive its rights record and checksums, and verify actual IMA/DICOM headers, spacing, orientation, field of view, artifact level and dental alignment. Check required structures in axial, coronal and sagittal planes. Preserve original coordinates, acquisition resolution and all registration transforms.

Only then decide which structures can be segmented with evidence. Keep airspace masks distinct from tissue masks and record uncertain boundaries. If the tongue root, nasal region or palate are not adequately resolved, pause that structure and use a better same-person MRI/CT source or commission specialist reference-guided reconstruction with the uncertain regions explicitly marked. Do not stretch a sagittal contour, reuse legacy procedural meshes as segmentations, or treat smoothing as added anatomical evidence.

**Present blocker:** medical-image hosts are outside the execution environment's permitted network destinations. The browser research service can read several source pages, but runtime requests to Figshare/Zenodo APIs returned proxy 403. Dataset download/import and local image inspection therefore remain unverified. A viable next step is to enable the official download hosts through environment configuration or have the original archive supplied locally; no network bypass was attempted. Confirm the final redirected download host through supported configuration before acquisition.

**Approval requested:** authorize Stage 2 beginning with DVTD acquisition and scan suitability inspection. Approval is not a waiver of missing imaging evidence: segmentation must wait until the actual case passes inspection. If access remains blocked, Stage 2 stops at acquisition rather than substituting procedural anatomy.
