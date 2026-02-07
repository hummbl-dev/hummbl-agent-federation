/**
 * Federation VS Code Extension
 */

import * as vscode from 'vscode';
import { FederationClient } from '@hummbl/federation-sdk';

let statusBarItem: vscode.StatusBarItem;
let client: FederationClient;

export function activate(context: vscode.ExtensionContext) {
    console.log('Federation extension activated');

    // Initialize client
    const config = vscode.workspace.getConfiguration('federation');
    const apiKey = config.get<string>('apiKey') || '';
    const baseUrl = config.get<string>('baseUrl');

    if (apiKey) {
        client = new FederationClient({ apiKey, baseUrl });
    }

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.command = 'federation.switchProvider';
    updateStatusBar('Ready', 0);
    statusBarItem.show();

    // Register commands
    const routeSelection = vscode.commands.registerCommand(
        'federation.routeSelection',
        routeSelectionHandler
    );

    const switchProvider = vscode.commands.registerCommand(
        'federation.switchProvider',
        switchProviderHandler
    );

    const compareProviders = vscode.commands.registerCommand(
        'federation.compareProviders',
        compareProvidersHandler
    );

    context.subscriptions.push(
        routeSelection,
        switchProvider,
        compareProviders,
        statusBarItem
    );
}

async function routeSelectionHandler() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.document.getText(editor.selection);
    if (!selection) {
        vscode.window.showWarningMessage('No selection');
        return;
    }

    if (!client) {
        vscode.window.showErrorMessage('Federation API key not configured');
        return;
    }

    updateStatusBar('Routing...', undefined, true);

    try {
        const response = await client.route({
            prompt: selection,
        });

        updateStatusBar(response.provider, response.cost);

        // Show result in output channel
        const channel = vscode.window.createOutputChannel('Federation');
        channel.appendLine(`Provider: ${response.provider}`);
        channel.appendLine(`Cost: $${response.cost.toFixed(4)}`);
        channel.appendLine(`Latency: ${response.latencyMs}ms`);
        channel.appendLine('---');
        channel.appendLine(response.content);
        channel.show();

    } catch (error) {
        vscode.window.showErrorMessage(`Routing failed: ${error}`);
        updateStatusBar('Error', undefined);
    }
}

async function switchProviderHandler() {
    const providers = [
        { label: '$(zap) Groq — Fastest', provider: 'groq' },
        { label: '$(credit-card) DeepSeek — Cheapest', provider: 'deepseek' },
        { label: '$(star) OpenAI — Best Quality', provider: 'openai' },
        { label: '$(shield) Anthropic — Safest', provider: 'anthropic' },
        { label: '$(home) Ollama — Local', provider: 'ollama' },
    ];

    const selected = await vscode.window.showQuickPick(providers, {
        placeHolder: 'Select provider',
    });

    if (selected) {
        vscode.window.showInformationMessage(`Switched to ${selected.provider}`);
        updateStatusBar(selected.provider, undefined);
    }
}

async function compareProvidersHandler() {
    vscode.window.showInformationMessage('Provider comparison coming soon');
}

function updateStatusBar(
    provider: string,
    cost?: number,
    loading: boolean = false
) {
    const icon = loading ? '$(sync~spin)' : '$(hub)';
    const costStr = cost !== undefined ? `$${cost.toFixed(2)}` : '';
    statusBarItem.text = `${icon} ${provider} ${costStr}`;
    statusBarItem.tooltip = 'Click to switch provider';
}

export function deactivate() {
    console.log('Federation extension deactivated');
}
