/**
 * Hides the whole header bar to prevent unwanted navigation.
 */
function hideApplicationHeader() {
    const hideOnceExists = setInterval(function() {
        const headers = document.getElementsByTagName('header');
        if (headers.length) {
            // the header bar now exists so we can remove it
            headers[0].remove();
            clearInterval(hideOnceExists);
        }
    }, 100);
}

/**
 * Hide the cluster name as that is already shown in Cura's header bar.
 */
function hideClusterName() {
    const hideOnceExists = setInterval(function() {
        const headers = document.getElementsByClassName('print-jobs_cluster-name');
        if (headers.length) {
            // the header bar now exists so we can remove it
            headers[0].remove();
            clearInterval(hideOnceExists);
        }
    }, 100);
}

document.addEventListener('DOMContentLoaded', function() {
    hideApplicationHeader();
    hideClusterName();
}, false);
