// Experiment Types

export interface Experiment {
	id: string;
	type: 'full' | 'stage_run';
	hasStatistics: boolean;
	hasCompleteContext: boolean;
	contextFiles: string[];
	timestamp?: string;
}

export interface ExperimentContext {
	state: ContextState;
	stage_contexts: StageContexts;
	history_length: number;
}

export interface ContextState {
	current_stage: string | null;
	completed_stages: string[];
	stage_outputs: StageOutputs;
	idea: Idea | null;
	research: Validation | null;
	legal_insights: LegalInsights | null;
	prototype: PrototypeInfo | null;
	marketing_strategies: MarketingStrategy[] | null;
	pitch: PitchDeck | null;
	decisions: Decision[];
	rejections: Rejection[];
	iterations: number;
	conversations: Conversation[];
	tool_calls: ToolCall[];
	start_time: string;
	costs: CostInfo;
	token_usage: TokenUsage;
	experiment_dir?: string;
	experiment_name?: string;
	chairman_input?: string;
}

export interface StageContexts {
	idea_development: Record<string, unknown>;
	prototyping: Record<string, unknown>;
	pitch: Record<string, unknown>;
}

export interface StageOutputs {
	idea_development?: IdeaDevelopmentOutput;
	prototyping?: PrototypingOutput;
	pitch?: PitchOutput;
}

// Idea Development Types

export interface IdeaDevelopmentOutput {
	idea: Idea;
	final_validation: Validation;
	legal_insights?: LegalInsights;
	iteration_count?: number;
	converged?: boolean;
}

export interface Idea {
	problem: string;
	solution: string;
	target_market: string;
	value_proposition: string;
	novelty: string;
	market_size_estimate: string;
	competitive_advantage: string;
}

export interface Validation {
	market_analysis: string;
	competitors: Competitor[];
	market_size: MarketSize;
	risks: string[];
	opportunities: string[];
	recommendation: 'GO' | 'PIVOT' | 'PASS' | 'NO-GO';
	reasoning: string;
}

export interface Competitor {
	name: string;
	description: string;
	strengths: string;
	weaknesses: string;
}

export interface MarketSize {
	TAM: string;
	SAM: string;
	SOM: string;
	sources: string;
}

export interface LegalInsights {
	// New format fields
	overall_risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
	blocking_issues?: BlockingIssue[];
	key_risks?: KeyRisk[];
	recommendations?: LegalRecommendation[];
	// Legacy format fields
	ip_analysis?: IPAnalysis | string;
	regulatory_requirements?: RegulatoryRequirement[] | string;
	privacy_compliance?: PrivacyCompliance | string;
	liability_assessment?: string;
	licensing_requirements?: string;
}

export interface BlockingIssue {
	issue: string;
	severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
	resolution_path: string;
}

export interface KeyRisk {
	category: string;
	risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
	summary: string;
}

export interface LegalRecommendation {
	priority: number;
	action: string;
	category: string;
}

export interface IPAnalysis {
	patent_landscape: string;
	trademark_considerations: string;
	trade_secrets: string;
}

export interface RegulatoryRequirement {
	name: string;
	jurisdiction: string;
	applicability: string;
	compliance_requirements: string[];
	estimated_cost: string;
}

export interface PrivacyCompliance {
	applicable_laws: string[];
	key_requirements: string[];
	estimated_cost?: string;
}

// Prototyping Types

export interface PrototypingOutput {
	prototype: PrototypeInfo;
	architecture: Architecture;
	design: Design;
	final_designs?: FinalDesign[];
	qa_results?: QAResults;
}

export interface PrototypeInfo {
	directory: string;
	files_generated: number;
	tech_stack: TechStack;
	endpoints?: string[];
	status?: string;
}

export interface TechStack {
	frontend: TechChoice;
	backend: TechChoice;
	database: DatabaseChoice;
	infrastructure?: TechChoice;
}

export interface TechChoice {
	framework: string;
	language: string;
	rationale: string;
}

export interface DatabaseChoice {
	primary: string;
	caching?: string;
	rationale: string;
}

export interface Architecture {
	system_name: string;
	tech_stack: TechStack;
	core_components: CoreComponent[];
	data_flows: DataFlow[];
	api_structure: APIStructure;
	implementation_notes: string[];
	mvp_scope_summary: MVPScope;
}

export interface CoreComponent {
	name: string;
	responsibility: string;
	technology: string;
	key_features: string[];
}

export interface DataFlow {
	flow_name: string;
	steps: string[];
	components_involved: string[];
}

export interface APIStructure {
	base_url: string;
	endpoints: APIEndpoint[];
	authentication: string;
}

export interface APIEndpoint {
	path: string;
	method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
	purpose: string;
}

export interface MVPScope {
	in_scope: string[];
	out_of_scope: string[];
}

export interface Design {
	design_system: DesignSystem;
	user_flows: UserFlow[];
	wireframes: Wireframe[];
	component_library: ComponentDefinition[];
	design_rationale: string;
	implementation_notes: string;
}

export interface DesignSystem {
	colors: ColorPalette;
	typography: Typography;
	spacing: SpacingSystem;
	components: string[];
}

export interface ColorPalette {
	primary: string;
	secondary: string;
	accent: string;
	neutral?: Record<string, string>;
	semantic?: {
		success: string;
		warning: string;
		error: string;
	};
}

export interface Typography {
	font_families: Record<string, string>;
	sizes: Record<string, string>;
	weights: Record<string, number>;
}

export interface SpacingSystem {
	base_unit: string;
	scale: number[];
}

export interface UserFlow {
	flow_name: string;
	description: string;
	steps: string[];
	screens: string[];
}

export interface Wireframe {
	screen_name: string;
	description: string;
	components: string[];
	layout: string;
	interactions: string[];
	viewport: string;
}

export interface ComponentDefinition {
	component_name: string;
	description: string;
	props: Record<string, unknown>;
	states: string[];
}

export interface FinalDesign {
	screen_name: string;
	filepath: string;
	design_type: string;
	viewport: string;
	colors_used: {
		primary: string;
		secondary: string;
		accent: string;
	};
}

export interface QAResults {
	test_coverage: number;
	issues_found: number;
	issues_resolved: number;
	recommendations: string[];
}

// Pitch Types

export interface PitchOutput {
	marketing_strategies: MarketingStrategy[];
	pitch_deck: PitchDeck;
}

export interface MarketingStrategy {
	channel: string;
	target_audience: string;
	approach: string;
	budget_considerations: string;
	success_metrics: string;
}

export interface PitchDeck {
	title: string;
	tagline: string;
	slides: PitchSlide[];
}

export interface PitchSlide {
	slide_number: number;
	title: string;
	subtitle?: string;
	content: string;
	visual_suggestion: string;
	talking_points: string[];
}

// Statistics Types

export interface Statistics {
	total_execution_time_ms: number;
	total_calls: number;
	total_tokens: number;
	total_prompt_tokens: number;
	total_completion_tokens: number;
	total_cost: number;
	max_budget: number;
	budget_used_percent: number;
	stages: Record<string, StageStatistics>;
	agents: Record<string, AgentStatistics>;
}

export interface StageStatistics {
	execution_time_ms: number;
	total_calls: number;
	total_tokens: number;
	total_cost: number;
	agents: Record<string, AgentStatistics>;
}

export interface AgentStatistics {
	call_count: number;
	execution_time_ms: number;
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	cost: number;
}

// Test Result Types

export interface TestResult {
	id: string;
	stage_name?: string;
	test_name?: string;
	agent_name?: string;
	test_type?: string;
	timestamp: string;
	timestamp_start?: string;
	timestamp_end?: string;
	execution_time_ms?: number;
	success: boolean;
	input?: Record<string, unknown>;
	iterations?: TestIteration[];
	final_output?: Record<string, unknown>;
	events?: TestEvent[];
	error?: string | null;
	tools?: ToolDefinition[];
	tool_count?: number;
}

export interface TestIteration {
	iteration: number;
	agents: AgentExecution[];
}

export interface AgentExecution {
	agent_name: string;
	method: string;
	timestamp_start?: string;
	timestamp_end?: string;
	execution_time_ms: number;
	output: Record<string, unknown>;
}

export interface TestEvent {
	type: string;
	name?: string;
	passed?: boolean;
	timestamp?: string;
	details?: Record<string, unknown>;
}

export interface ToolDefinition {
	name: string;
	description: string;
	parameters: Record<string, unknown>;
}

// Helper Types

export interface Decision {
	agent: string;
	decision: string;
	reasoning: string;
	timestamp: string;
}

export interface Rejection {
	agent: string;
	reason: string;
	timestamp: string;
}

export interface Conversation {
	agent: string;
	message: string;
	timestamp: string;
}

export interface ToolCall {
	agent: string;
	tool: string;
	arguments: Record<string, unknown>;
	result: unknown;
	timestamp: string;
}

export interface CostInfo {
	total: number;
	by_stage: Record<string, number>;
}

export interface TokenUsage {
	total: number;
	by_agent: Record<string, number>;
}

// Stage Run Result (from results.json)

export interface StageRunResult {
	stage: string;
	input: string;
	success: boolean;
	experiment_dir: string;
	stage_output: Record<string, unknown>;
	full_context: ExperimentContext;
}
