# 🚀 Project Vault Template - Standard Structure

*Template for creating new project vaults in the Cortex multi-vault system*

## 📁 **Standard Project Vault Structure**

```
project-{name}/
├── .obsidian/                    # Obsidian configuration
├── 00-Meta/
│   ├── Project-Profile.md        # Project metadata and overview
│   ├── Tag-Schema.md            # Project-specific tag definitions
│   ├── Cross-Vault-Links.md     # AI-generated cross-vault connections
│   └── Vault-Settings.md        # Vault-specific settings
├── 01-Planning/                 # Project planning and strategy
│   ├── Project-Charter.md       # Project goals and scope
│   ├── Milestones.md           # Key milestones and deadlines
│   └── Resource-Planning.md     # Resource allocation and planning
├── 02-Development/              # Development logs and progress
│   ├── Development-Log.md       # Daily development progress
│   ├── Technical-Decisions.md   # Technical architecture decisions
│   └── Code-Reviews.md         # Code review notes and feedback
├── 03-Decisions/                # Project-specific ADRs
│   ├── ADR-001-Technology-Stack.md
│   └── ADR-002-Database-Choice.md
├── 04-Resources/                # Project resources and references
│   ├── Documentation/           # Project documentation
│   ├── References/             # External references and links
│   └── Tools-and-Setup.md      # Development tools and setup
├── 05-Insights/                 # Project-specific learnings
│   ├── Lessons-Learned.md      # Key lessons and insights
│   ├── Best-Practices.md       # Discovered best practices
│   └── Performance-Metrics.md   # Project performance data
└── 99-Archive/                  # Completed/archived items
    ├── Completed-Tasks.md       # Archived completed tasks
    └── Old-Versions.md         # Archived old versions
```

## 🏷️ **Standard Tag Schema**

### **Project Tags:**
- `#project-{name}` - Main project identifier
- `#planning` - Planning and strategy related
- `#development` - Development and implementation
- `#testing` - Testing and QA related
- `#deployment` - Deployment and infrastructure
- `#documentation` - Documentation related

### **Status Tags:**
- `#todo` - Tasks to be done
- `#in-progress` - Currently working on
- `#completed` - Finished tasks
- `#blocked` - Blocked tasks
- `#review` - Items under review

### **Priority Tags:**
- `#high-priority` - High priority items
- `#medium-priority` - Medium priority items
- `#low-priority` - Low priority items
- `#urgent` - Urgent items requiring immediate attention

### **Type Tags:**
- `#meeting` - Meeting notes
- `#decision` - Decision records
- `#bug` - Bug reports and fixes
- `#feature` - Feature development
- `#research` - Research and investigation

## 🤖 **AI Learning Integration**

### **Tag Correlation Learning:**
The AI system will automatically:
- Analyze tag usage patterns in this vault
- Find correlations with other project vaults
- Suggest related tags based on content
- Generate cross-vault link suggestions

### **Pattern Detection:**
- Identify successful project patterns
- Extract reusable best practices
- Correlate project outcomes with approaches
- Suggest improvements based on other projects

## 🔗 **Cross-Vault Connections**

### **Automatic Linking:**
- AI generates `Cross-Vault-Links.md` in `00-Meta/`
- Links to related content in other project vaults
- Suggestions based on tag correlations and content similarity
- Updated automatically every 6 hours

### **Manual Linking:**
- Create explicit links to hub vault insights
- Reference related decisions from other projects
- Link to shared resources and templates
- Connect to global best practices

## 📊 **Project Profile Template**

```markdown
# Project Profile: {Project Name}

## 📋 **Basic Information**
- **Project Name:** {Name}
- **Start Date:** {Date}
- **Expected Completion:** {Date}
- **Status:** {Planning/Development/Testing/Deployment/Completed}
- **Priority:** {High/Medium/Low}

## 🎯 **Project Goals**
- {Goal 1}
- {Goal 2}
- {Goal 3}

## 🏷️ **Primary Tags**
- #project-{name}
- #{technology-stack}
- #{project-type}
- #{priority-level}

## 👥 **Team & Stakeholders**
- **Project Lead:** {Name}
- **Team Members:** {Names}
- **Stakeholders:** {Names}

## 🔗 **Related Projects**
- Link to similar projects in other vaults
- Dependencies on other projects
- Shared resources with other projects

## 📈 **Success Metrics**
- {Metric 1}: {Target}
- {Metric 2}: {Target}
- {Metric 3}: {Target}
```

## 🛠️ **Vault Creation Commands**

### **Quick Project Setup:**
```bash
# Create and initialize new project vault
cortex create-project --name "project-name" --type "web-app"
```

### **Manual Setup Steps:**
2. **Set Up Project Profile:**
   - Fill out `Project-Profile.md` with project details
   - Define project-specific tags in `Tag-Schema.md`
   - Set vault preferences in `Vault-Settings.md`

3. **Initialize AI Learning:**
   - Add initial content with consistent tagging
   - Run AI analysis to establish baseline patterns
   - Review generated cross-vault connections

4. **Connect to Hub:**
   - Link relevant global insights from hub vault
   - Reference applicable ADRs and best practices
   - Set up cross-references to related projects

## 🔄 **Maintenance & Updates**

### **Daily:**
- Update development logs with consistent tagging
- Review AI-generated link suggestions
- Add new insights and learnings

### **Weekly:**
- Review and update project profile
- Analyze cross-vault connection suggestions
- Update tag schema if needed

### **Monthly:**
- Export project insights to hub vault
- Review and archive completed items
- Update success metrics and progress

---

**Template Version:** v1.0  
**Last Updated:** 2025-08-10  
**Compatible with:** Cortex v3.0 Multi-Vault System