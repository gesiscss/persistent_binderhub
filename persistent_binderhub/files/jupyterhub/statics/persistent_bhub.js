require(["jquery", "jhapi", "moment"], function($, JHAPI, moment) {
  "use strict";

  var base_url = window.jhdata.base_url;
  var user = window.jhdata.user;
  var api = new JHAPI(base_url);

  // Customize stop server button
  $("#stop").click(function() {
    $(this).text('Stopping')
           .attr("disabled", true)
           .attr("title", "Your server is stopping")
           .click(function() {
               return false;
           });
    // hide "My Server" button while stopping
    $(this).next('a').addClass('hidden');
    api.stop_server(user, {
      success: function() {
        $("#stop").hide();
        var ref = $('#stop').data('ref');
        $('#last-used-'+ref).text(moment().calendar());
        // change text from "My Server" to "Launch" and make all launch buttons visible
        $('.project-launch').attr('href', '#').text('Launch').removeClass('btn-primary').addClass('btn-warning').removeClass('hidden');
        $('.project-delete').removeClass('hidden');
      }
    });
  });

  // nice formatting for "Last used" column in projects table
  // copied from admin.js
  $(".time-col").map(function (i, el) {
    // convert ISO datestamps to nice momentjs ones
    el = $(el);
    if (el.text() !== "running" ) {
        let m = moment(new Date(el.text().trim()));
        //el.text(m.isValid() ? m.fromNow() : "never");
        el.text(m.isValid() ? m.calendar(): "never");
    }
  });
});


$(document).ready(function() {
    // Project launch through table
    $('.project-launch').click(function(e) {
        // if server is running, this button holds the url of the server
        // if server is not running, do following
        if ($(this).attr('href') === '#') {
            e.preventDefault();
            //$("#build-form").get(0).scrollIntoView();
            // fill the binder form with values of selected repo and submit
            var ref = $(this).prop('id').replace("launch-","");
            var repo_url = $(this).data('url');
            var repo_url_lower = repo_url.toLowerCase();
            var provider_prefix;
            var provider_prefix_selected;
            // TODO handle provider prefix for other providers
            if (repo_url_lower.indexOf('github.com') !== -1 && repo_url_lower.indexOf('gist.github.com') === -1) {
               provider_prefix = 'gh';
               provider_prefix_selected = 'GitHub';
            } else if (repo_url_lower.indexOf('gitlab.com') !== -1) {
               // gitlab.com
               provider_prefix = 'gl';
               provider_prefix_selected = 'GitLab.com';
            } else if (repo_url_lower.indexOf('gist.github.com') !== -1) {
               // gist.github.com
               provider_prefix = 'gist';
               provider_prefix_selected = 'Gist';
            } else {
               provider_prefix = 'git';
               provider_prefix_selected = 'Git repository';
            }
            $('#provider_prefix').val(provider_prefix);
            $('#provider_prefix-selected').text(provider_prefix_selected);
            $('#ref').val(ref);
            $('#repository').val(repo_url);
            $('#filepath').val('');
            $('button#submit').trigger('click');
            // hide all launch and delete buttons
            $('.project-launch').addClass('hidden');
            $('.project-delete').addClass('hidden');
            return false;
        }
    });

    // Project deletion
    // we would use show.bs.modal event instead of click: https://getbootstrap.com/docs/3.4/javascript/#modals-events
    // but it bootstrap methods fails because we load jquery after bootstrap js
    // see: https://stackoverflow.com/questions/25757968/bootstrap-modal-is-not-a-function
    $('.project-delete').on('click', function (event) {
        // reset parts of dialog
        $('#delete-project-body').children().removeClass("hidden");
        $('#delete-project-error').text('').addClass("hidden");
        $('#delete-on-disk').prop("checked", false);
        $('#delete-confirm').text("Delete now").removeClass("hidden").prop("disabled", true);
        // fill hidden inputs, they will be used in ajax call to delete project
        $('#delete-url').val($(this).data('url'));
        $('#delete-id').val($(this).prop('id'));  // this will be used in success return of ajax call to delete project row from table
        var project_name = $(this).data('name');
        $('#delete-name').val(project_name);
        // update text in confirm dialog
        $('#delete-project-label').text('Delete project: ' + project_name);
        $('#delete-project-text').text('Are you sure that you want to delete "' + project_name +'" project?');
    });
    $('#delete-on-disk').on('click', function (event) {
        // Enable/disable "Delete now" button according to delete-on-disk checkbox
        $('#delete-confirm').prop("disabled", !$(this).prop("checked"));
    });
    function display_error(message) {
        // display error message in modal
        $('#delete-project-body').children().addClass("hidden");
        $('#delete-project-error').text(message).removeClass("hidden");
        $('#delete-confirm').addClass("hidden");
    }
    $('#delete-project').on('hide.bs.modal', function (e) {
        // reset hidden inputs, when modal is closed
        $('#delete-url').val('');
        $('#delete-name').val('');
        $('#delete-id').val('');
    });
    $('#delete-confirm').on('click', function (event) {
        $('#delete-confirm').prop("disabled", true).text("Deleting");
        var body = JSON.stringify({repo_url: $('#delete-url').val(),
                                   name: $('#delete-name').val(),
                                   id: $('#delete-id').val()});
        var user_name = window.jhdata.user;
        var url = '/hub/api/projects/'+user_name;
        console.log(url, body);
        $.ajax({
            url: url,
            type: 'DELETE',
            data: body,
            success: function (response) {
                if ("error" in response) {
                    // show error message only, user should handle the error first
                    display_error(response['error']);
                } else {
                    // project is deleted
                    // remove project from "Your Projects" table

                    // jquery cant select by id if id contains dot inside, and we have this case for default project
                    // so use getElementById
                    //$("#"+response["id"]).closest('tr').remove();
                    $(document.getElementById(response["id"])).closest('tr').remove();
                    if ($('#your-projects tr').length === 1) {
                        // user has no projects, so remove empty projects table
                        $('#your-projects').addClass("hidden");
                        $('#no-projects').removeClass("hidden");
                        $('.projects-container').addClass("no-projects");
                    }
                    // close modal
                    // .modal fails because we load jquery after bootstrap js
                    // see: https://stackoverflow.com/questions/25757968/bootstrap-modal-is-not-a-function
                    //$('#delete-project').modal('hide');
                    $('#delete-close').trigger('click');
                }
                },
            error: function () {
                display_error("Error. Please refresh the page and try again.");
            }
        });
    });
});
