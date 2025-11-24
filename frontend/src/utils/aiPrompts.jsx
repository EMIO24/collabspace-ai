// AI Prompt Templates

export const SYSTEM_PROMPTS = {
  assistant: 'You are a helpful AI assistant for a project management application. Provide concise, actionable responses.',
  
  taskAnalyzer: 'You are an expert project manager. Analyze tasks and provide insights on priority, complexity, and time estimates.',
  
  meetingNotes: 'You are a professional meeting notes assistant. Create structured, well-organized notes from transcripts.',
  
  codeReviewer: 'You are an expert software engineer. Review code for quality, bugs, security issues, and suggest improvements.',
  
  insightsGenerator: 'You are a data analyst. Generate actionable insights from project data and metrics.',
};

export const generateTaskAnalysisPrompt = (task) => {
  return `Analyze this task and provide recommendations:

Title: ${task.title}
Description: ${task.description || 'No description'}
Current Priority: ${task.priority || 'Not set'}
Due Date: ${task.dueDate || 'Not set'}
Assignee: ${task.assignee?.name || 'Unassigned'}

Please provide:
1. Suggested priority level (low, medium, high) with reasoning
2. Estimated time to complete
3. Potential blockers or risks
4. Recommendations for successful completion`;
};

export const generateMeetingNotesPrompt = (transcript) => {
  return `Create structured meeting notes from this transcript:

${transcript}

Format the notes with these sections:
1. **Meeting Summary** (2-3 sentences)
2. **Key Discussion Points** (bullet points)
3. **Decisions Made** (bullet points)
4. **Action Items** (who, what, when)
5. **Next Steps**`;
};

export const generateCodeReviewPrompt = (code, language, context) => {
  return `Review this ${language} code:

${context ? `Context: ${context}\n\n` : ''}
\`\`\`${language}
${code}
\`\`\`

Please provide:
1. **Code Quality Assessment** (readability, maintainability)
2. **Potential Bugs or Issues**
3. **Security Concerns** (if any)
4. **Performance Considerations**
5. **Suggested Improvements**`;
};

export const generateInsightsPrompt = (dataType, data) => {
  const prompts = {
    productivity: `Analyze this productivity data and provide insights:

${JSON.stringify(data, null, 2)}

Identify:
1. Key trends and patterns
2. Areas of high/low performance
3. Bottlenecks or inefficiencies
4. Actionable recommendations`,

    teamPerformance: `Analyze this team performance data:

${JSON.stringify(data, null, 2)}

Provide:
1. Overall team health assessment
2. Individual performance highlights
3. Collaboration patterns
4. Recommendations for improvement`,

    projectHealth: `Analyze this project health data:

${JSON.stringify(data, null, 2)}

Assess:
1. Project status and trajectory
2. Risk factors
3. Resource allocation
4. Timeline feasibility
5. Success probability`,
  };

  return prompts[dataType] || prompts.productivity;
};

export const generateSmartSuggestions = (context) => {
  return `Based on the current context:

${JSON.stringify(context, null, 2)}

Provide 3-5 smart suggestions for:
1. Next actions to take
2. Potential improvements
3. Quick wins`;
};

export const generateTaskBreakdown = (task) => {
  return `Break down this task into smaller, manageable subtasks:

Title: ${task.title}
Description: ${task.description}

Create 3-7 subtasks with:
1. Clear, actionable titles
2. Estimated time for each
3. Logical sequence/dependencies`;
};

export const generateProjectRisks = (project) => {
  return `Identify potential risks for this project:

Name: ${project.name}
Description: ${project.description}
Timeline: ${project.startDate} to ${project.endDate}
Team Size: ${project.teamSize || 'Unknown'}

List:
1. Top 5 potential risks
2. Impact level (High/Medium/Low)
3. Mitigation strategies`;
};