module.exports = {
	locales: {
		'/': {
			lang: 'en-US',
			title: 'Crystal Toolkit',
			description: 'Crystal Toolkit is an interactive web app that allows you to import, view, analyze and transform crystal structures and molecules.'
		}
	},
	themeConfig: {
		displayAllHeaders: true,
		nav: [
			{ text: 'Home', link: '/' },
			{ text: 'Documentation', link: '/docs.md' },
			{ text: 'Open Web App', link: 'https://viewer.materialsproject.org/' },
		],
		sidebar: ['/', '/docs', '/docs-dev', '/changelog'],
		sidebarDepth: 2,
		lastUpdated: 'Last Updated',
		repo: 'materialsproject/crystaltoolkit',
		repoLabel: 'Contribute',
		docsRepo: 'materialsproject/crystaltoolkit',
		docsDir: 'docs',
		editLinks: true,
		editLinkText: 'Help improve this page'
  }
}