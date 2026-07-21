
function ConvertTo-GPFieldDefinition {
    param([hashtable]$Field,[hashtable]$Model)
    $f=@{
        InternalName=$Field.internalName; DisplayName=$Field.displayNameDE; Type=$Field.type
        Required=[bool]$Field.required; Indexed=[bool]$Field.indexed; EnforceUnique=[bool]$Field.unique
    }
    foreach($p in @('default','min','max','maxLength','numLines','allowMultiple','searchable','exportable','aiVisible')){
        if($Field.ContainsKey($p)){$f[$p]=$Field[$p]}
    }
    if($Field.choiceSet){
        $set=$Model.ChoiceSets|Where-Object key -eq $Field.choiceSet|Select-Object -First 1
        $f.ChoiceSet=$Field.choiceSet
        $f.Choices=@($set.values|ForEach-Object{$_[1]})
    }
    if($Field.lookupObject){
        $target=$Model.objectTypes | Where-Object { $_.key -eq $Field.lookupObject -or $_.source -eq $Field.lookupObject } | Select-Object -First 1
        if(-not $target){throw "Unknown lookup object '$($Field.lookupObject)' for $($Field.internalName)."}
        $f.LookupList=$target.source
    }
    return $f
}
function Get-GPFieldsForBaseClass {
    param([string]$BaseClass,[hashtable]$Model)
    $keys=@($Model.baseClasses[$BaseClass].fields)
    return @($Model.Fields|Where-Object{$keys -contains $_.key}|ForEach-Object{ConvertTo-GPFieldDefinition $_ $Model})
}
function Get-GPTechnicalSpecificFields {
    param([string]$ObjectKey,[hashtable]$Model)
    return @($Model.Fields|Where-Object{$_.appliesTo -and $_.appliesTo -contains $ObjectKey}|ForEach-Object{ConvertTo-GPFieldDefinition $_ $Model})
}
function New-GPMetaField { param($n,$d,$t,$r=$false,$i=$false) return @{InternalName=$n;DisplayName=$d;Type=$t;Required=[bool]$r;Indexed=[bool]$i;EnforceUnique=$false} }
function Get-GPMetadataFields {
    param([string]$Key)
    $defs=@{
      ObjectTypes=@(
       @('ObjectTypeKey','Objekttyp-Schlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('PluralNameDE','Plural','Text',$false,$false),@('SourceListTitle','Quellliste/-bibliothek','Text',$true,$true),@('ObjectPrefix','Präfix','Text',$false,$true),@('DomainKey','Domäne','Text',$false,$true),@('IconName','Icon','Text',$false,$false),@('PrimaryColor','Primärfarbe','Text',$false,$false),@('SecondaryColor','Sekundärfarbe','Text',$false,$false),@('StatusModelKey','Statusmodell','Text',$false,$true),@('BaseClass','Basisklasse','Text',$true,$true),@('ObjectKind','Objektart','Text',$true,$true),@('DefaultViewKey','Standardansicht','Text',$false,$true),@('DefaultFormKey','Standardformular','Text',$false,$true),@('DefaultRoleKey','Standardrolle','Text',$false,$true),@('AllowCreate','Anlegen erlaubt','Boolean',$false,$false),@('AllowDelete','Löschen erlaubt','Boolean',$false,$false),@('AllowAttachments','Anhänge erlaubt','Boolean',$false,$false),@('AllowRelations','Beziehungen erlaubt','Boolean',$false,$false),@('AllowComments','Kommentare erlaubt','Boolean',$false,$false),@('AllowVersioning','Versionierung erlaubt','Boolean',$false,$false),@('AIEnabled','KI aktiviert','Boolean',$false,$true)
      )
      FieldDefinitions=@(
       @('FieldDefinitionKey','Felddefinitionsschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('FieldInternalName','Interner Feldname','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('SharePointType','SharePoint-Feldtyp','Text',$true,$true),@('ChoiceSetKey','Auswahlliste','Text',$false,$true),@('LookupObjectTypeKey','Lookup-Objekttyp','Text',$false,$true),@('AllowMultiple','Mehrfachwerte','Boolean',$false,$false),@('IsIndexed','Indiziert','Boolean',$false,$false),@('ControlType','Steuerelementtyp','Text',$false,$true),@('SectionKey','Abschnitt','Text',$false,$true),@('IsRequired','Pflichtfeld','Boolean',$false,$false),@('IsReadOnly','Schreibgeschützt','Boolean',$false,$false),@('IsVisible','Sichtbar','Boolean',$false,$true),@('IsSearchable','Durchsuchbar','Boolean',$false,$true),@('IsExportable','Exportierbar','Boolean',$false,$true),@('IsAIVisible','Für KI sichtbar','Boolean',$false,$true),@('DefaultValue','Standardwert','Note',$false,$false),@('ValidationExpression','Validierung','Note',$false,$false),@('HelpTextDE','Hilfetext','Note',$false,$false)
      )
      FormDefinitions=@(
       @('FormDefinitionKey','Formularschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('FormMode','Formularmodus','Text',$true,$true),@('SectionKey','Abschnitt','Text',$true,$true),@('SectionTitleDE','Abschnittstitel','Text',$true,$false),@('GroupKey','Gruppe','Text',$false,$true),@('RowNumber','Zeile','Number',$false,$false),@('ColumnNumber','Spalte','Number',$false,$false),@('Width','Breite','Number',$false,$false),@('ColumnsDesktop','Spalten Desktop','Number',$false,$false),@('VisibleIf','Sichtbar wenn','Note',$false,$false),@('RequiredIf','Pflicht wenn','Note',$false,$false),@('EnabledIf','Aktiv wenn','Note',$false,$false),@('IsCollapsible','Einklappbar','Boolean',$false,$false),@('IsInitiallyExpanded','Initial geöffnet','Boolean',$false,$false)
      )
      FormFieldDefinitions=@(
       @('FormFieldDefinitionKey','Formularfeldschlüssel','Text',$true,$true),@('FormDefinitionKey','Formularschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('FormMode','Formularmodus','Text',$true,$true),@('SectionKey','Abschnitt','Text',$true,$true),@('FieldInternalName','Interner Feldname','Text',$true,$true),@('RowNumber','Zeile','Number',$false,$false),@('ColumnNumber','Spalte','Number',$false,$false),@('Width','Breite','Number',$false,$false),@('VisibleIf','Sichtbar wenn','Note',$false,$false),@('RequiredIf','Pflicht wenn','Note',$false,$false),@('EnabledIf','Aktiv wenn','Note',$false,$false),@('OverrideLabelDE','Abweichende Beschriftung','Text',$false,$false)
      )
      PageDefinitions=@(
       @('PageKey','Seitenschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('ScreenName','Screen','Text',$true,$true),@('PageType','Seitentyp','Text',$true,$true),@('IconName','Icon','Text',$false,$false),@('Route','Route','Text',$false,$true),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true)
      )
      NavigationDefinitions=@(
       @('NavigationKey','Navigationsschlüssel','Text',$true,$true),@('ParentNavigationKey','Übergeordneter Eintrag','Text',$false,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('PageKey','Seite','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$false,$true),@('IconName','Icon','Text',$false,$false),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true),@('IsVisible','Sichtbar','Boolean',$false,$true)
      )
      DashboardDefinitions=@(
       @('DashboardKey','Dashboard-Schlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('PageKey','Seite','Text',$true,$true),@('LayoutType','Layout','Text',$true,$true),@('RefreshSeconds','Aktualisierung (Sekunden)','Number',$false,$false),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true)
      )
      WidgetDefinitions=@(
       @('WidgetKey','Widget-Schlüssel','Text',$true,$true),@('DashboardKey','Dashboard','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('WidgetType','Widget-Typ','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$false,$true),@('ViewDefinitionKey','Ansicht','Text',$false,$true),@('MetricKey','Kennzahl','Text',$false,$true),@('Position','Position','Number',$false,$true),@('Width','Breite','Number',$false,$false),@('Height','Höhe','Number',$false,$false),@('DrilldownPageKey','Drilldown-Seite','Text',$false,$true)
      )
      CommandDefinitions=@(
       @('CommandKey','Befehlsschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('IconName','Icon','Text',$false,$false),@('CommandContext','Kontext','Text',$true,$true),@('ActionType','Aktionstyp','Text',$true,$true),@('TargetPageKey','Zielseite','Text',$false,$true),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true),@('RequiresConfirmation','Bestätigung erforderlich','Boolean',$false,$false)
      )
      ValidationDefinitions=@(
       @('ValidationKey','Validierungsschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('FieldInternalName','Interner Feldname','Text',$false,$true),@('RuleType','Regeltyp','Text',$true,$true),@('Expression','Ausdruck','Note',$true,$false),@('MessageDE','Meldung','Note',$true,$false),@('Severity','Schweregrad','Text',$true,$true)
      )
      BusinessRuleDefinitions=@(
       @('BusinessRuleKey','Geschäftsregelschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('TriggerType','Trigger','Text',$true,$true),@('ConditionExpression','Bedingung','Note',$false,$false),@('ActionType','Aktionstyp','Text',$true,$true),@('TargetField','Zielfeld','Text',$false,$true),@('ParametersJson','Parameter','Note',$false,$false),@('Priority','Priorität','Number',$false,$true)
      )
      TextResources=@(
       @('ResourceKey','Ressourcenschlüssel','Text',$true,$true),@('LanguageCode','Sprache','Text',$true,$true),@('ResourceText','Text','Note',$true,$false),@('ResourceContext','Kontext','Text',$false,$true)
      )
      ViewDefinitions=@(
       @('ViewDefinitionKey','Ansichtsschlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('FilterExpression','Filter','Note',$false,$false),@('SortDefinition','Sortierung','Note',$false,$false),@('ColumnDefinition','Spalten','Note',$false,$false),@('GroupByField','Gruppierung','Text',$false,$true),@('IsDefault','Standardansicht','Boolean',$false,$true),@('IsPersonalizable','Personalisierbar','Boolean',$false,$false)
      )
      WorkflowDefinitions=@(
       @('WorkflowKey','Workflow-Schlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('TriggerType','Trigger','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('ActionType','Aktion','Text',$true,$true),@('StatusModelKey','Statusmodell','Text',$false,$true),@('FromStatusKey','Von Status','Text',$false,$true),@('ToStatusKey','Nach Status','Text',$false,$true),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true),@('NotificationTemplateKey','Benachrichtigungsvorlage','Text',$false,$true),@('ParametersJson','Parameter','Note',$false,$false)
      )
      AIPrompts=@(
       @('PromptKey','Prompt-Schlüssel','Text',$true,$true),@('ObjectTypeKey','Objekttyp','Text',$true,$true),@('Purpose','Zweck','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('PromptTemplate','Promptvorlage','Note',$true,$false),@('Provider','Anbieter','Text',$false,$true),@('Model','Modell','Text',$false,$true),@('Temperature','Temperatur','Number',$false,$false)
      )
      AISkills=@(
       @('SkillKey','Skill-Schlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('Purpose','Zweck','Text',$true,$true),@('AllowedObjectTypes','Erlaubte Objekttypen','Note',$true,$false),@('PromptKey','Prompt','Text',$true,$true),@('WriteTarget','Schreibziel','Text',$false,$true),@('RequiresApproval','Freigabe erforderlich','Boolean',$false,$true)
      )
      PermissionDefinitions=@(
       @('PermissionKey','Berechtigungsschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('SharePointRole','SharePoint-Rolle','Text',$true,$true),@('CanCreate','Anlegen','Boolean',$false,$false),@('CanEdit','Bearbeiten','Boolean',$false,$false),@('CanDelete','Löschen','Boolean',$false,$false),@('CanApprove','Freigeben','Boolean',$false,$false)
      )
      StatusModels=@(
       @('StatusModelKey','Statusmodell','Text',$true,$true),@('StatusKey','Statusschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('IsInitial','Initialstatus','Boolean',$false,$false),@('IsFinal','Endstatus','Boolean',$false,$false),@('AllowedNextStatusKeys','Erlaubte Folgestatus','Note',$false,$false),@('RequiresApproval','Freigabe erforderlich','Boolean',$false,$true),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true),@('WorkflowKey','Workflow','Text',$false,$true),@('NotificationKey','Benachrichtigung','Text',$false,$true)
      )
      ChoiceValues=@(
       @('ChoiceSetKey','Auswahlliste','Text',$true,$true),@('ChoiceKey','Auswahlschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('Color','Farbe','Text',$false,$false),@('IconName','Icon','Text',$false,$false),@('ParentChoiceKey','Übergeordnete Auswahl','Text',$false,$true),@('IsDefault','Standardwert','Boolean',$false,$false)
      )
      RelationTypes=@(
       @('RelationTypeKey','Relationstyp','Text',$true,$true),@('SourceObjectTypeKey','Quellobjekttyp','Text',$true,$true),@('TargetObjectTypeKey','Zielobjekttyp','Text',$true,$true),@('LabelDE','Bezeichnung','Text',$true,$false),@('InverseLabelDE','Inverse Bezeichnung','Text',$false,$false),@('AllowMultiple','Mehrfach erlaubt','Boolean',$false,$false),@('IsDirectional','Gerichtet','Boolean',$false,$false)
      )
      AppSettings=@(
       @('SettingKey','Einstellungsschlüssel','Text',$true,$true),@('SettingValue','Wert','Note',$false,$false),@('SettingType','Datentyp','Text',$false,$true),@('Category','Kategorie','Text',$false,$true)
      )
      CanvasAppErrors=@(
       @('ErrorTimestamp','Fehlerzeitpunkt','DateTime',$true,$true),@('UserEmail','Benutzer','Text',$false,$true),@('ScreenName','Screen','Text',$false,$true),@('ActionName','Aktion','Text',$false,$true),@('ObjectTypeKey','Objekttyp','Text',$false,$true),@('ItemID','Element-ID','Number',$false,$true),@('ErrorKind','Fehlerart','Text',$false,$true),@('ErrorMessage','Fehlermeldung','Note',$true,$false),@('Resolved','Gelöst','Boolean',$false,$true)
      )
      AppRoles=@(
       @('RoleKey','Rollenschlüssel','Text',$true,$true),@('Member','Mitglied','User',$true,$true),@('RoleName','Rollenname','Text',$true,$true),@('ValidUntil','Gültig bis','DateTime',$false,$true)
      )
      SearchIndex=@(
       @('SearchObjectTypeKey','Objekttyp','Text',$true,$true),@('SearchItemID','Element-ID','Number',$true,$true),@('SearchGovernanceID','Governance-ID','Text',$false,$true),@('SearchTitle','Titel','Text',$true,$true),@('SearchSummary','Zusammenfassung','Note',$false,$false),@('SearchKeywords','Suchbegriffe','Note',$false,$false),@('SearchOwnerEmail','Verantwortlich','Text',$false,$true),@('SearchStatusKey','Status','Text',$false,$true),@('SearchModifiedAt','Geändert am','DateTime',$false,$true)
      )
      TimelineEvents=@(
       @('TimelineObjectTypeKey','Objekttyp','Text',$true,$true),@('TimelineItemID','Element-ID','Number',$true,$true),@('TimelineGovernanceID','Governance-ID','Text',$false,$true),@('TimelineEventType','Ereignistyp','Text',$true,$true),@('TimelineEventAt','Ereigniszeitpunkt','DateTime',$true,$true),@('TimelineEventBy','Ausgeführt von','User',$false,$true),@('TimelineSummary','Zusammenfassung','Text',$true,$false),@('TimelineDetails','Details','Note',$false,$false),@('CorrelationID','Korrelations-ID','Text',$false,$true)
      )
      NotificationTemplates=@(
       @('TemplateKey','Vorlagenschlüssel','Text',$true,$true),@('Channel','Kanal','Text',$true,$true),@('SubjectDE','Betreff','Text',$false,$false),@('BodyDE','Nachricht','Note',$true,$false),@('Severity','Priorität','Text',$false,$true)
      )
      StatusPresentation=@(
       @('PresentationKey','Darstellungsschlüssel','Text',$true,$true),@('StatusModelKey','Statusmodell','Text',$true,$true),@('StatusKey','Statusschlüssel','Text',$true,$true),@('ForegroundColor','Textfarbe','Text',$false,$false),@('BackgroundColor','Hintergrundfarbe','Text',$false,$false),@('IconName','Icon','Text',$false,$false),@('IsClosed','Abgeschlossen','Boolean',$false,$true)
      )
      SavedViews=@(
       @('SavedViewKey','Ansichtsschlüssel','Text',$true,$true),@('DisplayNameDE','Anzeigename','Text',$true,$false),@('ObjectTypeKey','Objekttyp','Text',$false,$true),@('FilterExpression','Filter','Note',$false,$false),@('SortDefinition','Sortierung','Note',$false,$false),@('ColumnDefinition','Spalten','Note',$false,$false),@('Owner','Besitzer','User',$false,$true),@('RequiredRoleKey','Erforderliche Rolle','Text',$false,$true),@('IsShared','Geteilt','Boolean',$false,$true),@('IsDefault','Standard','Boolean',$false,$true)
      )
      UserPreferences=@(
       @('UserPreferenceKey','Einstellungsschlüssel','Text',$true,$true),@('User','Benutzer','User',$true,$true),@('PreferenceKey','Präferenz','Text',$true,$true),@('PreferenceValue','Wert','Note',$false,$false)
      )
      NotificationsLog=@(
       @('NotificationKey','Benachrichtigungsschlüssel','Text',$true,$true),@('NotificationType','Typ','Text',$true,$true),@('ObjectGovernanceID','Objekt-Governance-ID','Text',$false,$true),@('SentAt','Gesendet am','DateTime',$false,$true),@('Recipient','Empfänger','Text',$false,$true),@('Status','Status','Text',$false,$true)
      )
    }
    if(-not $defs.ContainsKey($Key)){return @()}
    return @($defs[$Key]|ForEach-Object{New-GPMetaField $_[0] $_[1] $_[2] $_[3] $_[4]})
}
function Get-GPViewsForObject {
    param([hashtable]$Object,[hashtable]$Model)
    $views=[System.Collections.Generic.List[hashtable]]::new()
    foreach($v in $Model.Views){
        $match=($v.objectTypeKey -eq '*') -or ($v.objectTypeKey -eq $Object.key) -or ($v.objectTypeKey -eq $Object.baseClass)
        if(-not $match){continue}
        $fields=@($v.columns)
        if($Object.kind -eq 'Library'){
            $fields=@($fields|ForEach-Object{if($_ -eq 'Title'){'LinkFilename'}else{$_}})
        } else {
            $fields=@($fields|ForEach-Object{if($_ -eq 'Title'){'LinkTitle'}else{$_}})
        }
        $views.Add(@{Name=$v.displayNameDE;Key=$v.key;Fields=$fields;Filter=$v.filter;Sort=@($v.sort);GroupBy=$v.groupBy;IsDefault=[bool]$v.isDefault})
    }
    return @($views)
}
function Compile-GPArchitecture {
    [CmdletBinding()]
    param([Parameter(Mandatory)][hashtable]$Model)
    $lists=[System.Collections.Generic.List[hashtable]]::new()
    foreach($o in $Model.objectTypes){
        $fields=[System.Collections.Generic.List[hashtable]]::new()
        foreach($f in Get-GPFieldsForBaseClass $o.baseClass $Model){$fields.Add($f)}
        foreach($f in $Model.ObjectFields|Where-Object objectTypeKey -eq $o.key){$fields.Add((ConvertTo-GPFieldDefinition $f $Model))}
        $template=if($o.kind -eq 'Library'){'DocumentLibrary'}else{'GenericList'}
        $lists.Add(@{Title=$o.source;Template=$template;ObjectKey=$o.key;BaseClass=$o.baseClass;Fields=@($fields);Views=(Get-GPViewsForObject $o $Model);Settings=@{Versioning=[bool]$o.allowVersioning;Attachments=[bool]$o.allowAttachments}})
    }
    foreach($o in $Model.technicalObjects){
        $fields=[System.Collections.Generic.List[hashtable]]::new()
        foreach($f in Get-GPFieldsForBaseClass $o.baseClass $Model){$fields.Add($f)}
        foreach($f in Get-GPTechnicalSpecificFields $o.key $Model){$fields.Add($f)}
        foreach($f in Get-GPMetadataFields $o.key){$fields.Add($f)}
        $unique=@{};$dedup=[System.Collections.Generic.List[hashtable]]::new()
        foreach($f in $fields){if(-not $unique.ContainsKey($f.InternalName)){$unique[$f.InternalName]=$true;$dedup.Add($f)}}
        $lists.Add(@{Title=$o.title;Template='GenericList';ObjectKey=$o.key;BaseClass=$o.baseClass;Fields=@($dedup);Views=@(@{Name='Aktive Einträge';Fields=@('LinkTitle','Modified');Filter='';Sort=@(@('Modified','desc'));GroupBy='';IsDefault=$true})})
    }
    return @{SchemaVersion=$Model.schemaVersion;Lists=@($lists);Navigation=@($Model.navigation);Runtime=@{Views=@($Model.Views);Workflows=@($Model.Workflows);AIPrompts=@($Model.AIPrompts);AISkills=@($Model.AISkills);Permissions=@($Model.Permissions);Pages=@($Model.Pages);NavigationDefinitions=@($Model.NavigationDefinitions);Dashboards=@($Model.Dashboards);Widgets=@($Model.Widgets);Commands=@($Model.Commands);Validations=@($Model.Validations);BusinessRules=@($Model.BusinessRules);TextResources=@($Model.TextResources)}}
}
Export-ModuleMember -Function Compile-GPArchitecture
