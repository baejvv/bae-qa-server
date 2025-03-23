module.exports = async ({github, context, core}) => {

  ////////////////////////////////////
  // retrieve workflow run data
  ////////////////////////////////////
  console.log("get workflow run")
  const wf_run = await github.rest.actions.getWorkflowRun({
    owner: context.repo.owner,
    repo: context.repo.repo,
    run_id: context.runId
  })
  console.log(wf_run.data)
  console.log("get jobs for workflow run:", wf_run.data.jobs_url)
  const jobs_response = await github.request(wf_run.data.jobs_url)

  ////////////////////////////////////
  // build slack notification message
  ////////////////////////////////////

  // some utility functions
  var date_diff_func = function(start, end) {
    var duration = end - start
    // format the duration
    var delta = duration / 1000
    var days = Math.floor(delta / 86400)
    delta -= days * 86400
    var hours = Math.floor(delta / 3600) % 24
    delta -= hours * 3600
    var minutes = Math.floor(delta / 60) % 60
    delta -= minutes * 60
    var seconds = Math.floor(delta % 60)
    var format_func = function(v, text, check) {
      if (v <= 0 && check) {
        return ""
      } else {
        return v + text
      }
    }
    return format_func(days, "d", true) + format_func(hours, "h", true) + format_func(minutes, "m", true) + format_func(seconds, "s", false)
  }
  var status_icon_func = function(s) {
    switch (s) {
      case "w_success":
        return ":white_check_mark:"
      case "w_failure":
        return ":no_entry:"
      case "w_cancelled":
        return ":white_check_mark:"
      case "success":
        return "\u2713"
      case "failure":
        return "\u2717"
      default:
        return "\u20e0"
    }
  }
  const commit = context.sha.substr(0, 6)
  var pr = ""
  for (p of wf_run.data.pull_requests) {
    pr += ",<"+ p.url + "|#" + p.number + ">"
  }
  if (pr != "") {
    pr = "for " + pr.substr(1)
  }

  // build the message
  var is_wf_success = true
  var is_wf_failure = false
  var build_count = 0
  var max_block = 10
  var fetch_fields = []
  var build_fields = []
  var finish_fields = []
  var fetch_message = ""
  var build_message = ""
  var finish_message = ""
  for (j of jobs_response.data.jobs) {
    console.log(j.name, ":", j.status, j.conclusion, j.started_at, j.completed_at)
    // ignore the current job running this script
    if (j.status != "completed") {
      continue
    }
    if (j.conclusion != "success") {
      is_wf_success = false
    }
    if (j.conclusion == "failure") {
      is_wf_failure = true
    }

    if (j.name.startsWith("build")) {
      build_count += 1
    }

    if (j.name.startsWith("fetch")) {
      fetch_message += status_icon_func(j.conclusion) + " <" + j.html_url + "|" + j.name + ">\n  \u21b3 completed in " + date_diff_func(new Date(j.started_at), new Date(j.completed_at)) + "\n"
    } else if (j.name.startsWith("build") && build_count <= max_block ) {
      build_message += status_icon_func(j.conclusion) + " <" + j.html_url + "|" + j.name + ">\n  \u21b3 completed in " + date_diff_func(new Date(j.started_at), new Date(j.completed_at)) + "\n"
    } else if (!j.name.startsWith("build")) {
      finish_message += status_icon_func(j.conclusion) + " <" + j.html_url + "|" + j.name + ">\n  \u21b3 completed in " + date_diff_func(new Date(j.started_at), new Date(j.completed_at)) + "\n"
    }
  }

  if (fetch_message != null) {
    fetch_fields.push({
      type: "mrkdwn",
      text: fetch_message
    })
  }

  build_message = build_message == "" ? "no_build" : build_message;
  if (build_message != null) {
    build_fields.push({
      type: "mrkdwn",
      text: build_message
    })
  }
  if (finish_message != null) {
    finish_fields.push({
      type: "mrkdwn",
      text: finish_message
    })
  }

  var workflow_status = "w_cancelled"
  if (is_wf_success) {
    workflow_status = "w_success"
  } else if (is_wf_failure) {
    workflow_status = "w_failure"
  }

  var slack_msg = {
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: "<" + context.payload.repository.html_url + "|*" + context.payload.repository.full_name + "*>\nfrom *" + context.ref + "@" + commit + "*"
        }
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: status_icon_func(workflow_status) + " *" + context.workflow + "* " + pr + "\nWorkflow run <" + wf_run.data.html_url + "|#" + wf_run.data.run_number + "> completed in " + date_diff_func(new Date(wf_run.data.created_at), new Date(wf_run.data.updated_at))
        }
      },
      {
        type: "divider"
      },
      {
        type: "section",
        fields: fetch_fields
      },
      {
        type: "divider"
      },
      {
        type: "section",
        fields: build_fields
      },
      {
        type: "divider"
      },
      {
        type: "section",
        fields: finish_fields
      },
    ]
  }
  core.exportVariable('SLACK_MSG', slack_msg)
}
