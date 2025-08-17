<script lang="ts">
    import { onMount } from "svelte";
    import { auth } from "../auth";
    import { getResource, deleteResource } from "../api";

    export let resource: string;
    export let onRefresh: () => void;

    interface ResourceItem {
        id?: number;
        slug?: string;
        login?: string;
        title?: string;
    }

    let items: ResourceItem[] = [];
    let userRole: "guest" | "admin" = "guest";

    $: auth.subscribe((a) => (userRole = a.role));

    async function load() {
        items = await getResource<ResourceItem>(resource);
    }

    async function remove(id: string | number) {
        await deleteResource(resource, id);
        await load();
        onRefresh();
    }

    onMount(load);
</script>

<h2>{resource}</h2>
<ul>
    {#each items as item}
        <li>
            {item.login ?? item.title}
            {#if userRole === "admin"}
                <button on:click={() => remove(item.id ?? item.slug!)}
                    >Удалить</button
                >
            {/if}
        </li>
    {/each}
</ul>
