<script lang="ts">
  import ResourceList from "./components/ResourceList.svelte";
  import ResourceForm from "./components/ResourceForm.svelte";
  import LoginForm from "./components/LoginForm.svelte";
  import { auth, logout } from "./auth";

  import { onMount } from "svelte";
  onMount(() => {
    import("./auth").then((m) => m.loadToken());
  });

  let currentResource: string = "admins";
  let refreshKey: number = 0;

  function refresh() {
    refreshKey += 1;
  }
</script>

<select bind:value={currentResource}>
  <option value="admins">Admins</option>
  <option value="pages">Pages</option>
</select>

{#if $auth.role === "guest"}
  <LoginForm />
{:else}
  <button on:click={logout}>Logout</button>
  <ResourceForm resource={currentResource} onSave={refresh} item={{}} />
{/if}

{#key refreshKey}
  <ResourceList resource={currentResource} onRefresh={refresh} />
{/key}
