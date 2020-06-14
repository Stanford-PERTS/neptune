# Neptune Dashboard Features

## Organization Search

Ability to search for organizations by name.

![](assets/neptune-dashboard-org-search.png)

## Program Select

Ability to select the program you'd like to view.

![](assets/neptune-dashboard-program-select.png)

## Filters

Ability to filter participating organizations based on criteria. These can be combined. So, for example, you can select organizations that have been approved but that have not yet submitted an LoA.

![](assets/neptune-dashboard-filters.png)

## Sorting

Ability to sort on columns. You can sort within a filtered list.

![](assets/neptune-dashboard-sort-columns.png)

## Match Count

Ability to see the number of organizations that match the selected criteria.

![](assets/neptune-dashboard-match-count.png)

## Organization POID

Ability to update an organization's POID.

![](assets/neptune-dashboard-poid.png)

## Liaison Information

Ability to view liaison information.

![](assets/neptune-dashboard-liaison.png)

## Liaison Contact List

Ability to retrieve contacts information for the liaisons of multiple organizations.

First, select the organizations you'd like to contact.

![](assets/neptune-dashboard-select-boxes.png)

Then, click the email icon located in the table header row.

![](assets/neptune-dashboard-email-icon.png)

You'll be provided with a list of liaison names, liaison emails, and organizations of the selected rows. This can be copy and pasted directly into a Google Spreadsheet.

![](assets/neptune-dashboard-email-list-tsv.png)

You can also select CSV to receive an email only list, separated by commas, that can be copy and pasted into a Gmail BCC list.

![](assets/neptune-dashboard-email-list-csv.png)

## Approve / Reject an Organization

Ability to approve / reject an organization. To approve or reject an organization, hover over the **Approved?** status indicator.

![](assets/neptune-dashboard-org-approve.png)

Then, select to approve (`thumbs-up` icon) or reject (`reject` icon).

![](assets/neptune-dashboard-org-approve-hover.png)

By default, rejected organizations won't appear on the dashboard, but you can view them by setting the **Org Rejected** filter to **Yes** or **Any**.

![](assets/neptune-dashboard-view-rejected-orgs.png)

## Letter of Agreements

Ability to view Letter of Agreements. When a Letter of Agreement has been submitted, a `file` icon will appear in the **LoA Submitted?** column. Click on the icon to view the attachment.

![](assets/neptune-dashboard-loa-view.png)

## Approve / Reject a Letter of Agreement

Ability to approve / reject a Letter of Agreement. When a Letter of Agreement has been submitted, along with the `file` icon that appears, a `[No]` status indicator will appear in the **LoA Approved?** column. To approve or reject, hover over this status indicator.

![](assets/neptune-dashboard-loa-approve.png)

Then, select to approve (`thumbs-up` icon) or reject (`reject` icon).

**Note**: at the moment, you also need to add an Organiztion POID for an organization to be marked complete in the tasklist. This is important since the tasklist status will determine if an organization can proceed with participation.

![](assets/neptune-dashboard-loa-approve-hover.png)

### Rejected

If you reject a Letter of Agreement, it will be removed from the dashboard...

![](assets/neptune-dashboard-loa-did-reject.png)

...and a note will appear in the tasklist leting organization members know they will need to submit revisions.

![](assets/neptune-tasklist-loa-rejected.png)

### Approved

If you approve an Letter of Agreement, a `[Yes]` status indicator will appear in the **LoA Approved?** column.

![](assets/neptune-dashboard-loa-did-approve.png)
