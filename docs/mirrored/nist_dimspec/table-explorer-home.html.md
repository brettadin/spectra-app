# Table Explorer

To facilitate visual exploration of the DIMSpec database schema, a web application was written in Shiny. It served as proof-of-concept for the database/API/shiny approach and was used as the basic skeleton of the template app that ships with the project.

Table Explorer is a simple entity viewer for the attached database. Combining the comment decorations in DIMSpec and reading of entity definitions from the database (see [Inspecting Database Properties](instructions.html#inspecting-database-properties)) allows for R to expose a wealth of information about the underlying schema and quickly change which entity is being viewed. See [Shiny Applications](technical-details.html#shiny-applications) for details of how to launch this app, but the easiest method is after the `compliance.R` script has been executed, use `start_app("table_explorer")` to launch it in your preferred browser.

## Table Viewer

There is only one page for interactive content, named âTable Viewerâ ([Figure 1](table-explorer-home.html#fig03-01)). A navigation bar on the left controls the current page being viewed; collapse the bar using the âhamburgerâ icon (three short horizontal lines stacked on top of one another) at the top next to the NIST logo. Click the drop down box ([Figure 2 - left](table-explorer-home.html#fig03-02)) to change the database table or view being displayed. This will update the definition narrative immediately below the selection box ([Figure 2 - right](table-explorer-home.html#fig03-02)) and display the contents of that table ([Figure 3](table-explorer-home.html#fig03-03)).

---

![](assets/fig03-01_table_view_screen.png "Figure 1. The Table Explorer main page.")

Figure 1. The Table Explorer main page.

---

![](assets/fig03-02-entity_selector_and_definition.png "Figure 2. Choose a database entity (left) for information about its definition (right).")

Figure 2. Choose a database entity (left) for information about its definition (right).

---

![](assets/fig03-03_table_display.png "Figure 3. Data held in the selected entity.")

Figure 3. Data held in the selected entity.

---

## Entity Relationship Diagram

A full graphical representation of the entity relationship diagram is also provided. Click [here](assets/ERD.png) to open this graphic in full resolution in a new tab.

---

![](assets/fig03-04_erd.png "Figure 4. Entity Relationship Diagram")

Figure 4. Entity Relationship Diagram

---