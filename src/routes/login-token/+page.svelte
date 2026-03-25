<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const redirectParam = params.get('redirect');
		const token = localStorage.getItem('token');

		if (!redirectParam) {
			goto('/' + redirectParam);
			return;
		}

		let targetUrl;
		try {
			targetUrl = new URL(redirectParam, window.location.origin);
		} catch {
			goto('/');
			return;
		}

		if (!token) {
			goto(`/auth?redirect=${encodeURIComponent(window.location.href)}`);
		}

		targetUrl.searchParams.set('token', token);
		window.location.replace(targetUrl.toString());
	});
</script>
