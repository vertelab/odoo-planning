/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { patch } from "@web/core/utils/patch";

/**
 * Day Tasks: activity kanban record behaviour.
 *
 * Ported from the Odoo 14 legacy patch that extended ``web.KanbanRecord``.
 * In Odoo 18 the kanban record is an OWL component and the legacy
 * ``_openRecord`` override becomes a patch of ``onGlobalClick``.
 *
 * On a ``mail.activity`` card that carries the project kanban boxes, the
 * first box link is followed instead of opening the activity form: the boxes
 * are the primary action on those cards.
 *
 * The Odoo 14 ``selectionMode`` guard is dropped — multi-select kanban was
 * removed from the web client in Odoo 17.
 */
patch(KanbanRecord.prototype, {
    /**
     * @override
     */
    onGlobalClick(ev) {
        const { record } = this.props;
        if (record.resModel === "mail.activity") {
            const boxes = this.rootRef.el?.querySelectorAll(".o_project_kanban_boxes a");
            if (boxes?.length) {
                boxes[0].click();
                return;
            }
        }
        return super.onGlobalClick(ev);
    },
});
