
$script:GPMetadataCache=@{}
$script:GPMetadataStats=@{}

function ConvertTo-GPComparableValue {
 param($Value)
 if($null -eq $Value){return ''}
 if($Value -is [bool]){return $Value.ToString().ToLowerInvariant()}
 if($Value -is [datetime]){return $Value.ToUniversalTime().ToString('o')}
 if($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]){
   return (@($Value)|ForEach-Object{ConvertTo-GPComparableValue $_}) -join ';'
 }
 return ([string]$Value).Trim()
}
function Initialize-GPMetadataListCache {
 param([Parameter(Mandatory)][string]$List,[Parameter(Mandatory)][string]$KeyField)
 if($script:GPMetadataCache.ContainsKey($List)){return}
 $started=Get-Date
 Write-GPLog ("Runtime metadata: loading {0}." -f $List) INFO
 $items=@(Get-PnPListItem -List $List -PageSize 2000 -ErrorAction Stop)
 $map=@{}
 foreach($item in $items){
   $key=[string]$item.FieldValues[$KeyField]
   if([string]::IsNullOrWhiteSpace($key)){continue}
   if($map.ContainsKey($key)){throw "Duplicate metadata key '$key' in $List ($KeyField)."}
   $map[$key]=$item
 }
 $script:GPMetadataCache[$List]=@{KeyField=$KeyField;Items=$map}
 $script:GPMetadataStats[$List]=[ordered]@{Existing=$items.Count;Create=0;Update=0;Unchanged=0;Started=$started}
 Write-GPLog ("Runtime metadata: {0} - {1} existing row(s)." -f $List,$items.Count) INFO
}
function Set-GPSeedRow {
 param([string]$List,[string]$KeyField,[hashtable]$Values)
 $keyValue=[string]$Values[$KeyField]
 if($global:GPContext.DryRun){Write-GPLog "Upsert metadata $List/$keyValue" DRYRUN;return}
 Initialize-GPMetadataListCache -List $List -KeyField $KeyField
 $cache=$script:GPMetadataCache[$List];$stats=$script:GPMetadataStats[$List]
 $item=$cache.Items[$keyValue]
 if($item){
   $changed=$false
   foreach($name in $Values.Keys){
     if((ConvertTo-GPComparableValue $item.FieldValues[$name]) -ne (ConvertTo-GPComparableValue $Values[$name])){$changed=$true;break}
   }
   if($changed){Set-PnPListItem -List $List -Identity $item.Id -Values $Values|Out-Null;$stats.Update++}else{$stats.Unchanged++}
 }else{
   $created=Add-PnPListItem -List $List -Values $Values
   $cache.Items[$keyValue]=$created;$stats.Create++
 }
}
function ConvertTo-GPJsonValue { param($Value) if($null -eq $Value){return ''}; return ($Value|ConvertTo-Json -Depth 20 -Compress) }
function Publish-GPMetadata {
 [CmdletBinding()]
 param([hashtable]$Model)
 $script:GPMetadataCache=@{}
 $script:GPMetadataStats=@{}
 $metadataStarted=Get-Date
 Write-GPLog 'Runtime metadata publication started.' INFO
 foreach($o in $Model.objectTypes){
   Set-GPSeedRow ObjectTypes ObjectTypeKey @{
     Title=$o.displayNameDE;ObjectTypeKey=$o.key;DisplayNameDE=$o.displayNameDE;PluralNameDE=$o.pluralNameDE
     SourceListTitle=$o.source;ObjectPrefix=$o.prefix;DomainKey=$o.domain;IconName=$o.icon;PrimaryColor=$o.primaryColor;SecondaryColor=$o.secondaryColor
     StatusModelKey=$o.statusModel;BaseClass=$o.baseClass;ObjectKind=$o.kind;SortOrder=$o.sortOrder
     DefaultViewKey=$o.defaultView;DefaultFormKey=$o.defaultForm;DefaultRoleKey=$o.defaultRole
     AllowCreate=[bool]$o.allowCreate;AllowDelete=[bool]$o.allowDelete;AllowAttachments=[bool]$o.allowAttachments
     AllowRelations=[bool]$o.allowRelations;AllowComments=[bool]$o.allowComments;AllowVersioning=[bool]$o.allowVersioning
     AIEnabled=[bool]$o.aiEnabled;IsActive=$true
   }
 }
 foreach($s in $Model.StatusModels){$i=0;foreach($state in $s.states){$i++;Set-GPSeedRow StatusModels StatusKey @{
   Title="$($s.key):$($state[0])";StatusModelKey=$s.key;StatusKey="$($s.key):$($state[0])";DisplayNameDE=$state[1];SortOrder=$i*10
   IsInitial=[bool]$state[2];IsFinal=[bool]$state[3];AllowedNextStatusKeys=($state[4]-join ';');RequiresApproval=$false;IsActive=$true
 }}}
 foreach($c in $Model.ChoiceSets){foreach($v in $c.values){
   $color=if($v.Count -gt 4){$v[4]}else{''};$icon=if($v.Count -gt 3){$v[3]}else{''}
   Set-GPSeedRow ChoiceValues ChoiceKey @{Title="$($c.key):$($v[0])";ChoiceSetKey=$c.key;ChoiceKey="$($c.key):$($v[0])";DisplayNameDE=$v[1];SortOrder=$v[2];IconName=$icon;Color=$color;IsDefault=$false;IsActive=$true}
 }}
 foreach($r in $Model.RelationTypes){Set-GPSeedRow RelationTypes RelationTypeKey @{
   Title=$r.labelDE;RelationTypeKey=$r.key;SourceObjectTypeKey=$r.source;TargetObjectTypeKey=$r.target;LabelDE=$r.labelDE;InverseLabelDE=$r.inverseLabelDE
   AllowMultiple=[bool]$r.multiple;IsDirectional=[bool]$r.directional;SortOrder=100;IsActive=$true
 }}
 foreach($o in $Model.objectTypes){
   $baseKeys=@($Model.baseClasses[$o.baseClass].fields)
   $allFields=@($Model.Fields|Where-Object{$baseKeys -contains $_.key})+@($Model.ObjectFields|Where-Object objectTypeKey -eq $o.key)
   $position=0
   foreach($f in $allFields){$position+=10;$key="$($o.key):$($f.internalName)"
     $section=if($f.section){$f.section}elseif($f.internalName -in @('Owner','DeputyOwner','BusinessOwner','TechnicalOwner','DataSteward','DocumentOwner')){'Ownership'}elseif($f.internalName -in @('GovernanceID','GovernanceStatus','Criticality','ComplianceScope','LastReviewDate','NextReviewDate','ReviewCycleMonths','IsActive','Tags','DocumentStatus','DocumentReviewDate')){'Governance'}else{'General'}
     Set-GPSeedRow FieldDefinitions FieldDefinitionKey @{
       Title=$f.displayNameDE;FieldDefinitionKey=$key;ObjectTypeKey=$o.key;FieldInternalName=$f.internalName;DisplayNameDE=$f.displayNameDE
       SharePointType=$f.type;ChoiceSetKey=$f.choiceSet;LookupObjectTypeKey=$f.lookupObject;AllowMultiple=[bool]$f.allowMultiple;IsIndexed=[bool]$f.indexed
       ControlType=$f.type;SectionKey=$section;SortOrder=if($f.sortOrder){$f.sortOrder}else{$position};IsRequired=[bool]$f.required;IsReadOnly=($f.internalName -in @('GovernanceID','DocumentGovernanceID'))
       IsVisible=if($f.ContainsKey('visible')){[bool]$f.visible}else{$true};IsSearchable=if($f.ContainsKey('searchable')){[bool]$f.searchable}else{$true};IsExportable=if($f.ContainsKey('exportable')){[bool]$f.exportable}else{$true}
       IsAIVisible=if($f.ContainsKey('aiVisible')){[bool]$f.aiVisible}else{$true};DefaultValue=if($f.ContainsKey('default')){[string]$f.default}else{''};ValidationExpression='';HelpTextDE='';IsActive=$true
     }
   }
 }
 foreach($form in $Model.Forms){foreach($sec in $form.sections){$key="$($form.objectTypeKey):$($form.mode):$($sec.key)";Set-GPSeedRow FormDefinitions FormDefinitionKey @{
   Title=$sec.titleDE;FormDefinitionKey=$key;ObjectTypeKey=$form.objectTypeKey;FormMode=$form.mode;SectionKey=$sec.key;SectionTitleDE=$sec.titleDE
   SortOrder=$sec.sortOrder;ColumnsDesktop=$sec.columnsDesktop;IsCollapsible=$true;IsInitiallyExpanded=[bool]$sec.expanded;IsActive=$true
 }}}
 foreach($v in $Model.Views){Set-GPSeedRow ViewDefinitions ViewDefinitionKey @{
   Title=$v.displayNameDE;ViewDefinitionKey="$($v.objectTypeKey):$($v.key)";ObjectTypeKey=$v.objectTypeKey;DisplayNameDE=$v.displayNameDE
   FilterExpression=$v.filter;SortDefinition=(ConvertTo-GPJsonValue $v.sort);ColumnDefinition=(ConvertTo-GPJsonValue $v.columns)
   GroupByField=$v.groupBy;IsDefault=[bool]$v.isDefault;IsPersonalizable=[bool]$v.personalizable;SortOrder=100;IsActive=$true
 }}
 foreach($w in $Model.Workflows){Set-GPSeedRow WorkflowDefinitions WorkflowKey @{
   Title=$w.displayNameDE;WorkflowKey=$w.key;DisplayNameDE=$w.displayNameDE;TriggerType=$w.trigger;ObjectTypeKey=$w.objectTypeKey
   ActionType=$w.action;StatusModelKey=$w.statusModel;FromStatusKey=$w.fromStatus;ToStatusKey=$w.toStatus;RequiredRoleKey=$w.requiredRole
   NotificationTemplateKey=$w.notificationTemplate;ParametersJson=(ConvertTo-GPJsonValue $w.parameters);SortOrder=100;IsActive=[bool]$w.enabled
 }}
 foreach($p in $Model.AIPrompts){Set-GPSeedRow AIPrompts PromptKey @{
   Title=$p.displayNameDE;PromptKey=$p.key;ObjectTypeKey=$p.objectTypeKey;Purpose=$p.purpose;DisplayNameDE=$p.displayNameDE
   PromptTemplate=$p.template;Provider=$p.provider;Model=$p.model;Temperature=$p.temperature;SortOrder=100;IsActive=[bool]$p.enabled
 }}
 foreach($s in $Model.AISkills){Set-GPSeedRow AISkills SkillKey @{
   Title=$s.displayNameDE;SkillKey=$s.key;DisplayNameDE=$s.displayNameDE;Purpose=$s.purpose;AllowedObjectTypes=($s.allowedObjectTypes -join ';')
   PromptKey=$s.promptKey;WriteTarget=$s.writeTarget;RequiresApproval=[bool]$s.requiresApproval;SortOrder=100;IsActive=[bool]$s.enabled
 }}
 foreach($p in $Model.Permissions){Set-GPSeedRow PermissionDefinitions PermissionKey @{
   Title=$p.displayNameDE;PermissionKey=$p.key;DisplayNameDE=$p.displayNameDE;SharePointRole=$p.sharePointRole
   CanCreate=[bool]$p.canCreate;CanEdit=[bool]$p.canEdit;CanDelete=[bool]$p.canDelete;CanApprove=[bool]$p.canApprove;SortOrder=100;IsActive=$true
 }}
 foreach($o in $Model.objectTypes){
   $formKey="$($o.key):Edit"
   $baseKeys=@($Model.baseClasses[$o.baseClass].fields)
   $allFields=@($Model.Fields|Where-Object{$baseKeys -contains $_.key})+@($Model.ObjectFields|Where-Object objectTypeKey -eq $o.key)
   $row=0
   foreach($f in $allFields){$row++;$section=if($f.section){$f.section}elseif($f.internalName -in @('Owner','DeputyOwner','BusinessOwner','TechnicalOwner','DataSteward','DocumentOwner')){'Ownership'}elseif($f.internalName -in @('GovernanceID','GovernanceStatus','Criticality','ComplianceScope','LastReviewDate','NextReviewDate','ReviewCycleMonths','IsActive','Tags','DocumentStatus','DocumentReviewDate')){'Governance'}else{'General'}
     $key="$($o.key):Edit:$($f.internalName)";Set-GPSeedRow FormFieldDefinitions FormFieldDefinitionKey @{Title=$f.displayNameDE;FormFieldDefinitionKey=$key;FormDefinitionKey=$formKey;ObjectTypeKey=$o.key;FormMode='Edit';SectionKey=$section;FieldInternalName=$f.internalName;RowNumber=$row;ColumnNumber=1;Width=1;SortOrder=$row*10;IsActive=$true}
   }
 }
 foreach($p in $Model.Pages){Set-GPSeedRow PageDefinitions PageKey @{Title=$p.displayNameDE;PageKey=$p.key;DisplayNameDE=$p.displayNameDE;ScreenName=$p.screenName;PageType=$p.pageType;IconName=$p.icon;Route=$p.route;RequiredRoleKey=$p.requiresRole;SortOrder=$p.sortOrder;IsActive=[bool]$p.enabled}}
 foreach($n in $Model.NavigationDefinitions){Set-GPSeedRow NavigationDefinitions NavigationKey @{Title=$n.displayNameDE;NavigationKey=$n.key;ParentNavigationKey=$n.parentKey;DisplayNameDE=$n.displayNameDE;PageKey=$n.pageKey;ObjectTypeKey=$n.objectTypeKey;IconName=$n.icon;RequiredRoleKey=$n.requiresRole;IsVisible=[bool]$n.visible;SortOrder=$n.sortOrder;IsActive=$true}}
 foreach($d in $Model.Dashboards){Set-GPSeedRow DashboardDefinitions DashboardKey @{Title=$d.displayNameDE;DashboardKey=$d.key;DisplayNameDE=$d.displayNameDE;PageKey=$d.pageKey;LayoutType=$d.layout;RefreshSeconds=$d.refreshSeconds;RequiredRoleKey=$d.requiresRole;SortOrder=100;IsActive=[bool]$d.enabled}}
 foreach($w in $Model.Widgets){Set-GPSeedRow WidgetDefinitions WidgetKey @{Title=$w.displayNameDE;WidgetKey=$w.key;DashboardKey=$w.dashboardKey;DisplayNameDE=$w.displayNameDE;WidgetType=$w.widgetType;ObjectTypeKey=$w.objectTypeKey;ViewDefinitionKey=$w.viewKey;MetricKey=$w.metric;Position=$w.position;Width=$w.width;Height=$w.height;DrilldownPageKey=$w.drilldownPageKey;SortOrder=$w.position;IsActive=[bool]$w.enabled}}
 foreach($c in $Model.Commands){Set-GPSeedRow CommandDefinitions CommandKey @{Title=$c.displayNameDE;CommandKey=$c.key;DisplayNameDE=$c.displayNameDE;IconName=$c.icon;CommandContext=$c.context;ActionType=$c.actionType;TargetPageKey=$c.targetPageKey;RequiredRoleKey=$c.requiresRole;RequiresConfirmation=[bool]$c.confirm;SortOrder=$c.sortOrder;IsActive=[bool]$c.enabled}}
 foreach($v in $Model.Validations){Set-GPSeedRow ValidationDefinitions ValidationKey @{Title=$v.messageDE;ValidationKey=$v.key;ObjectTypeKey=$v.objectTypeKey;FieldInternalName=$v.fieldInternalName;RuleType=$v.ruleType;Expression=$v.expression;MessageDE=$v.messageDE;Severity=$v.severity;SortOrder=$v.sortOrder;IsActive=[bool]$v.enabled}}
 foreach($b in $Model.BusinessRules){Set-GPSeedRow BusinessRuleDefinitions BusinessRuleKey @{Title=$b.key;BusinessRuleKey=$b.key;ObjectTypeKey=$b.objectTypeKey;TriggerType=$b.trigger;ConditionExpression=$b.condition;ActionType=$b.actionType;TargetField=$b.targetField;ParametersJson=$b.parametersJson;Priority=$b.priority;SortOrder=$b.priority;IsActive=[bool]$b.enabled}}
 foreach($t in $Model.TextResources){Set-GPSeedRow TextResources ResourceKey @{Title=$t.key;ResourceKey="$($t.language):$($t.key)";LanguageCode=$t.language;ResourceText=$t.text;ResourceContext=$t.context;Description=$t.description;SortOrder=100;IsActive=$true}}
 # Derived status presentation for the Canvas App.
 foreach($statusModel in $Model.StatusModels){
   $position=0
   foreach($state in $statusModel.states){
     $position+=10
     $key="$($statusModel.key):$($state[0])"
     $isInitial=[bool]$state[2];$isFinal=[bool]$state[3]
     $foreground=if($isFinal){'#107C10'}elseif($isInitial){'#323130'}else{'#005A9E'}
     $background=if($isFinal){'#DFF6DD'}elseif($isInitial){'#F3F2F1'}else{'#DEECF9'}
     Set-GPSeedRow StatusPresentation PresentationKey @{Title=$state[1];PresentationKey=$key;StatusModelKey=$statusModel.key;StatusKey=$state[0];ForegroundColor=$foreground;BackgroundColor=$background;IconName=if($isFinal){'Completed'}else{'StatusCircleRing'};IsClosed=$isFinal;SortOrder=$position;IsActive=$true}
   }
 }
 foreach($v in @(
   @{k='MyOpenObjects';n='Meine offenen Einträge';o='*';f='Owner eq @Me and IsActive eq true'},
   @{k='DueReviews';n='Fällige Reviews';o='Review';f='ReviewDate le @Today+30'},
   @{k='CriticalRisks';n='Kritische Risiken';o='Risk';f='RiskLevel eq Critical'},
   @{k='OpenMeasures';n='Offene Maßnahmen';o='Measure';f='IsActive eq true'},
   @{k='RecentChanges';n='Letzte Changes';o='Change';f='IsActive eq true'}
 )){Set-GPSeedRow SavedViews SavedViewKey @{Title=$v.n;SavedViewKey=$v.k;DisplayNameDE=$v.n;ObjectTypeKey=$v.o;FilterExpression=$v.f;SortDefinition='';ColumnDefinition='';IsShared=$true;IsDefault=$false;SortOrder=100;IsActive=$true}}
 foreach($t in @(
   @{k='ReviewDue';c='Email';s='Review fällig: {GovernanceID}';b='Die Prüfung für {Title} ist fällig.';v='Warning'},
   @{k='RiskCritical';c='Teams';s='Kritisches Risiko: {GovernanceID}';b='Das Risiko {Title} wurde als kritisch eingestuft.';v='Critical'},
   @{k='MeasureOverdue';c='Email';s='Maßnahme überfällig: {GovernanceID}';b='Die Maßnahme {Title} ist überfällig.';v='Warning'},
   @{k='ChangeApproval';c='Email';s='Change-Freigabe: {GovernanceID}';b='Der Change {Title} wartet auf Freigabe.';v='Information'},
   @{k='ValidationFailed';c='Teams';s='Datenqualitätsfehler: {GovernanceID}';b='Für {Title} wurden Validierungsfehler festgestellt.';v='Warning'},
   @{k='GenericError';c='Teams';s='Governance Platform Fehler';b='Bei der Verarbeitung ist ein Fehler aufgetreten. CorrelationID: {CorrelationID}';v='Error'}
 )){Set-GPSeedRow NotificationTemplates TemplateKey @{Title=$t.k;TemplateKey=$t.k;Channel=$t.c;SubjectDE=$t.s;BodyDE=$t.b;Severity=$t.v;SortOrder=100;IsActive=$true}}
 foreach($s in @(
   @{k='App.Title';v=$Model.platformName;t='Text';c='App'},
   @{k='App.DefaultLanguage';v=$Model.frontendLanguage;t='Text';c='App'},
   @{k='Platform.SchemaVersion';v=$Model.schemaVersion;t='Version';c='Platform'},
   @{k='AI.Enabled';v='false';t='Boolean';c='AI'},
   @{k='Relations.UseCentralGraph';v='true';t='Boolean';c='Relations'},
   @{k='Runtime.MetadataVersion';v='6.2.5';t='Version';c='Runtime'}
 )){Set-GPSeedRow AppSettings SettingKey @{Title=$s.k;SettingKey=$s.k;SettingValue=$s.v;SettingType=$s.t;Category=$s.c;SortOrder=100;IsActive=$true}}
 if(-not $global:GPContext.DryRun){
   foreach($listName in @($script:GPMetadataStats.Keys|Sort-Object)){
     $stats=$script:GPMetadataStats[$listName];$duration=(Get-Date)-$stats.Started
     Write-GPLog ("Runtime metadata {0}: existing={1}, create={2}, update={3}, unchanged={4}, duration={5:hh\:mm\:ss}" -f $listName,$stats.Existing,$stats.Create,$stats.Update,$stats.Unchanged,$duration) INFO
   }
 }
 $duration=(Get-Date)-$metadataStarted
 Write-GPLog ("Runtime metadata publication completed. Duration: {0:hh\:mm\:ss}." -f $duration) SUCCESS
}
Export-ModuleMember -Function Publish-GPMetadata
