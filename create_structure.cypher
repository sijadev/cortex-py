// Create Folders
MERGE (f1:Folder {name: "Projects", path: "/Projects"});
MERGE (f2:Folder {name: "Research", path: "/Research"});

// Create Templates
MERGE (t1:Template {name: "ProjectTemplate"});
MERGE (t2:Template {name: "ResearchTemplate"});

// Create Tags
MERGE (tag1:Tag {name: "AI"});
MERGE (tag2:Tag {name: "Graph"});

// Create Notes with YAML and Aliases
CREATE (n1:Note {
  name: "ProjektA",
  aliases: ["PA", "Project Alpha"],
  yaml: {owner: "Alice", status: "active"},
  created: date("2025-08-14"),
  modified: date("2025-08-14")
});
CREATE (n2:Note {
  name: "ProjektB",
  aliases: ["PB"],
  yaml: {owner: "Bob", status: "planned"},
  created: date("2025-08-13"),
  modified: date("2025-08-14")
});

// Link Notes to Folders
MATCH (n1:Note {name: "ProjektA"}), (f1:Folder {name: "Projects"}) MERGE (n1)-[:IN_FOLDER]->(f1);
MATCH (n2:Note {name: "ProjektB"}), (f1:Folder {name: "Projects"}) MERGE (n2)-[:IN_FOLDER]->(f1);

// Link Notes to Templates
MATCH (n1:Note {name: "ProjektA"}), (t1:Template {name: "ProjectTemplate"}) MERGE (n1)-[:USES_TEMPLATE]->(t1);
MATCH (n2:Note {name: "ProjektB"}), (t1:Template {name: "ProjectTemplate"}) MERGE (n2)-[:USES_TEMPLATE]->(t1);

// Link Notes to Tags
MATCH (n1:Note {name: "ProjektA"}), (tag1:Tag {name: "AI"}) MERGE (n1)-[:TAGGED_WITH]->(tag1);
MATCH (n2:Note {name: "ProjektB"}), (tag2:Tag {name: "Graph"}) MERGE (n2)-[:TAGGED_WITH]->(tag2);

// Link Notes to each other
MATCH (n1:Note {name: "ProjektA"}), (n2:Note {name: "ProjektB"}) MERGE (n1)-[:LINKS_TO]->(n2);

// Example: Add more YAML properties
MATCH (n1:Note {name: "ProjektA"})
WITH n1, (CASE WHEN exists(n1.yaml) AND n1.yaml IS NOT NULL THEN n1.yaml ELSE {} END) AS yamlMap
SET n1.yaml = yamlMap + {priority: "high"};
