<script lang="ts">
    import { auth } from "../auth";
    import { createResource, updateResource } from "../api";

    export let resource: string;
    export let item: Record<string, any> = {};
    export let onSave: () => void = () => {};

    let data: Record<string, any> = { ...item };
    let userRole: "guest" | "admin" = "guest";

    $: auth.subscribe((a) => (userRole = a.role));

    async function save() {
        if (userRole !== "admin") return;

        if (item.id || item.slug) {
            await updateResource(resource, item.id ?? item.slug, data);
        } else {
            await createResource(resource, data);
        }
        onSave();
        data = {};
    }
</script>

{#if userRole === "admin"}
    <div>
        {#each Object.keys(data) as key}
            <input placeholder={key} bind:value={data[key]} />
        {/each}
        <button on:click={save}>Сохранить</button>
    </div>
{/if}
