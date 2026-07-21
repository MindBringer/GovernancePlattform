# Governance Platform 6.2.5 – Architecture Notes

## Single source of truth

The files in `architecture/` define both the physical SharePoint schema and the runtime behavior of the Canvas App, generic Power Automate flows and AI services.

| File | Responsibility |
|---|---|
| `platform.yaml` | object types, base classes, technical objects, navigation |
| `fields.yaml` | reusable physical field definitions |
| `object-fields.yaml` | object-specific fields and UI metadata |
| `choices.yaml` | controlled vocabularies |
| `status-models.yaml` | lifecycle state machines |
| `relations.yaml` | graph relation types |
| `forms.yaml` | dynamic form sections |
| `views.yaml` | SharePoint and Canvas views |
| `workflows.yaml` | generic workflow runtime configuration |
| `ai.yaml` | governed prompts and AI skills |
| `permissions.yaml` | application permission capabilities |

## Runtime model

A new object type should normally require only metadata changes. The intended runtime consists of generic screens:

- ObjectListScreen
- ObjectDetailsScreen
- DynamicEditScreen
- RelationScreen
- ReviewScreen
- SearchScreen

The Canvas App reads `ObjectTypes`, `FieldDefinitions`, `FormDefinitions`, `ViewDefinitions`, `StatusModels`, `ChoiceValues`, `RelationTypes` and `PermissionDefinitions`.

## Migration behavior

Provisioning is additive. Type changes require explicit migration rules. Version 6 aligns existing controlled fields such as SystemType, Environment, RiskCategory, ControlType and ApprovalStatus with SharePoint Choice fields rather than weakening them to free text.

## Operational boundary

This package provisions and seeds the SharePoint/runtime foundation. It does not import a Canvas App package or Power Automate solution. Those consumers are deliberately decoupled and use the provisioned metadata.
