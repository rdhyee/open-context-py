function showAnnotateItemInterface(type){
	/* shows an interface for annotating an item
	 * 
	*/
	var main_modal_title_domID = "myModalLabel";
	var main_modal_body_domID = "myModalBody";
	var title_dom = document.getElementById(main_modal_title_domID);
	var body_dom = document.getElementById(main_modal_body_domID);
	var actInterface = new annotateItemInterface(type);
	title_dom.innerHTML = actInterface.title;
	body_dom.innerHTML = actInterface.body;
	$("#myModal").modal('show');
}

function annotateItemInterface(type){
	if (type == 'author') {
		//make an interface for adding dc-terms:creator or dc-terms:contributor persons
		this.title = '<span class="glyphicon glyphicon-user" aria-hidden="true"></span>';
		this.title += ' Add Contributor and Creator (Authorship) Information';
		this.body = annotate_author_body();
	}
	else if (type == 'stableID') {
		//make an interface for adding stable identifiers
		this.title = '';
		this.title += ' Add a Stable / Persistent Identifier';
		this.body = annotate_stableID_body();
	}
}

function annotate_author_body(){
	
	var entityInterfaceHTML = "";
	/* changes global authorSearchObj from entities/entities.js */
	authorSearchObj = new searchEntityObj();
	authorSearchObj.name = "authorSearchObj";
	authorSearchObj.entities_panel_title = "Select Author or Editor";
	authorSearchObj.limit_item_type = "persons";
	authorSearchObj.limit_project_uuid = "0," + project_uuid;
	var afterSelectDone = {
		exec: function(){
				return authorObject();
			}
		};
	authorSearchObj.afterSelectDone = afterSelectDone;
	var entityInterfaceHTML = authorSearchObj.generateEntitiesInterface();
	console.log(authorSearchObj);
	
	var html = [
	'<div>',
	'<div class="row">',
	'<div class="col-xs-6">',
	'<label>Role / Relationship</label><br/>',
	'<label class="radio-inline">',
	'<input type="radio" name="pred-uri" id="new-anno-pred-uri-dc-contrib" ',
	'class="new-item-pred-uri" value="dc-terms:contributor" checked="checked">',
	'Contributor </label>',
	'<label class="radio-inline">',
	'<input type="radio" name="pred-uri" id="new-anno-pred-uri-dc-creator" ',
	'class="new-item-pred-uri" value="dc-terms:creator">',
	'Creator </label><br/><br/>',
	'<div class="form-group">',
	'<label for="new-anno-object-id">Person / Org. (Object ID)</label>',
	'<input id="new-anno-object-id" class="form-control input-sm"',
	'type="text" value="" />',
	'<span id="new-anno-object-label"></span>',
	'</div>',
	'<div class="form-group" id="new-anno-object-label-out">',
	'<label for="new-anno-object-label">Person / Org. (Object Label)</label>',
	'<input id="new-anno-object-label" class="form-control input-sm"',
	'type="text" disabled="disabled" value="Completed upon lookup to the right" />',
	'</div>',
	'<div class="form-group">',
	'<label for="new-anno-sort">Rank / Sort Order (0 = Unsorted)</label>',
	'<input id="new-anno-sort" class="form-control input-sm" style="width:20%;"',
	'type="text" value="0" />',
	'</div>',
	'<div class="form-group">',
	'<label for="new-anno-sort">Add Authorship Relation</label>',
	'<button class="btn btn-primary" onclick="addAuthorAnnotation();">Submit</button>',
	'</div>',
	'</div>',
	'<div class="col-xs-6">',
	entityInterfaceHTML,
	'</div>',
	'</div>',
	'<div class="row">',
	'<div class="col-xs-12">',
	'<small>Use <strong>contributor</strong> for persons or organizations with an overall secondary ',
	'role in making the content. Use <strong>creator</strong> for persons or organizations that ',
	'played more leading roles as directors, principle investigators or editors.',
	'<small>',
	'</div>',
	'</div>',
	'</div>'
	].join('\n');
	return html;
}

function authorObject(){
	// puts the selected item from the entity lookup interface
	// into the appropriate field for making a new assertion
	var obj_id = document.getElementById("authorSearchObj-sel-entity-id").value;
	var obj_label = document.getElementById("authorSearchObj-sel-entity-label").value;
	document.getElementById("new-anno-object-id").value = obj_id;
	//so we can edit disabled state fields
	var l_outer = document.getElementById("new-anno-object-label-out");
	var html = [
	'<label for="new-anno-object-label">Person / Org. (Object Label)</label>',
	'<input id="new-anno-object-label" class="form-control input-sm"',
	'type="text" disabled="disabled" value="' + obj_label + '" />'
	].join('\n');
	l_outer.innerHTML = html;
}

function addAuthorAnnotation(){
	//submits the new author annotation information
	var obj_id = document.getElementById("new-anno-object-id").value;
	if (obj_id.length > 0) {
		var sort_val = document.getElementById("new-anno-sort").value;
		var p_types = document.getElementsByClassName("new-item-pred-uri");
		for (var i = 0, length = p_types.length; i < length; i++) {
			if (p_types[i].checked) {
				var pred_uri = p_types[i].value;
			}
		}
		var url = "../../edit/add-item-annotation/" + encodeURIComponent(uuid);
		var req = $.ajax({
			type: "POST",
			url: url,
			dataType: "json",
			data: {
				sort: sort_val,
				predicate_uri: pred_uri,
				object_uri: obj_id,
				csrfmiddlewaretoken: csrftoken},
			success: addAuthorAnnotationDone
		});
	}
	else{
		alert("Need to select an author / editor first.");
	}
}

function addAuthorAnnotationDone(data){
	// reload the whole page from the server
	// it's too complicated to change all the instances of the item label on the page,
	// easier just to reload the whole page
	console.log(data);
	location.reload(true);
}

function annotate_stableID_body(){
	var html = [
	'<div>',
	'<div class="row">',
	'<div class="col-xs-8">',
	'<label>Stable ID Type</label><br/>',
	'<label class="radio-inline">',
	'<input type="radio" name="stable-id-type" id="stable-id-type-doi" ',
	'class="stable-id-type" value="doi" checked="checked" />',
	'DOI </label>',
	'<label class="radio-inline">',
	'<input type="radio" name="stable-id-type" id="stable-id-type-ark" ',
	'class="stable-id-type" value="ark" />',
	'ARK </label>',
	'<label class="radio-inline">',
	'<input type="radio" name="stable-id-type" id="stable-id-type-orcid" ',
	'class="stable-id-type" value="orcid" />',
	'ORCID </label><br/><br/>',
	'<div class="form-group">',
	'<label for="new-anno-object-id">Identifier</label>',
	'<input id="new-anno-object-id" class="form-control input-sm"',
	'type="text" value="" />',
	'</div>',
	'<div class="form-group">',
	'<label for="new-anno-sort">Add Identifier</label>',
	'<button class="btn btn-primary" onclick="addStableId();">Submit</button>',
	'</div>',
	'</div>',
	'<div class="col-xs-4">',
	'<h4>Notes on Stable Identifiers</h4>',
	'<p><small>Manually enter a stable / persistent identifier curated ',
	'by an external identifier service. Use EZID for items published by Open Context. ',
	'Use ORCID to identify persons.',
	'</small></p>',
	'</div>',
	'</div>',
	'</div>'
	].join('\n');
	return html;
}

function addStableId(){
	//submits the new stable identifier information
	var stable_id = document.getElementById("new-anno-object-id").value;
	if (stable_id.length > 0) {
		var id_types = document.getElementsByClassName("stable-id-type");
		for (var i = 0, length = id_types.length; i < length; i++) {
			if (id_types[i].checked) {
				var stable_type = id_types[i].value;
			}
		}
		var url = "../../edit/add-item-stable-id/" + encodeURIComponent(uuid);
		var req = $.ajax({
			type: "POST",
			url: url,
			dataType: "json",
			data: {
				stable_type: stable_type,
				stable_id: stable_id,
				csrfmiddlewaretoken: csrftoken},
			success: addStableIdDone
		});
	}
	else{
		alert("Need to add the identifier first.");
	}
}

function addStableIdDone(data){
	console.log(data);
	location.reload(true);
}