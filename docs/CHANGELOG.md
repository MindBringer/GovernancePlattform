# Changelog

## 6.2.5 – Git baseline candidate

- Added explicit SharePoint authentication modes: `-Interactive`, `-DeviceLogin`, and `-OSLogin`.
- Added authentication-stage logging before the blocking PnP login call.
- Aligned all runtime role references with PermissionDefinitions.
- Corrected the published-document filter to the stored German SharePoint choice value.
- Added `Changes.ApprovedDate` required by the approval business rule.
- Normalized child navigation URLs to the target Governance Portal site.
- Enforced uniqueness for stable governance and configuration keys.
- Added static architecture consistency checks for role references, field references, navigation URLs, and choice-based filters.

## 6.2.4

- Initial 50-list metadata-driven provisioning candidate.
- Added Canvas runtime metadata, search index, timeline, notification templates, saved views, and user preferences.
- Corrected PowerShell parser errors from 6.2.3.

## v1.0.0-alpha.3.0

- Metadata-driven application framework
- Framework dashboard and metadata views
- Editor bootstrap based on form definitions
