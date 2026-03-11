import re

with open(r'c:\ICOM\Database\dashboard_php\index.php', 'r', encoding='utf-8') as f:
    code = f.read()

# Patches for index.php RBAC
code = code.replace(
'''    if ($rest_ajax) {
        $q .= " WHERE restaurante = :rest";
        $p['rest'] = $rest_ajax;
    }''',
'''    if ($rest_ajax && can_access_restaurant($rest_ajax)) {
        $q .= " WHERE restaurante = :rest";
        $p['rest'] = $rest_ajax;
    } elseif (!is_owner()) {
        $allowed = $_SESSION['gi_allowed'] ?? [];
        if (empty($allowed)) {
            $q .= " WHERE 1=0";
        } elseif (!in_array('ALL', $allowed)) {
            $inStrs = [];
            foreach($allowed as $i => $ar) {
                $pname = "ajax_rest_$i";
                $inStrs[] = ":$pname";
                $p[$pname] = $ar;
            }
            $q .= " WHERE restaurante IN (" . implode(',', $inStrs) . ")";
        }
    }'''
)

code = code.replace(
'''$todos_los_restaurantes = $stmt_all_restaurantes->fetchAll(PDO::FETCH_COLUMN);''',
'''$todos_los_restaurantes_raw = $stmt_all_restaurantes->fetchAll(PDO::FETCH_COLUMN);
$todos_los_restaurantes = array_filter($todos_los_restaurantes_raw, 'can_access_restaurant');

// RBAC Global Params
$rbac_clause = "";
$rbac_v_clause = "";
$rbac_params = [];
if (!is_owner() && !in_array("ALL", $_SESSION['gi_allowed'] ?? [])) {
    $allowed = $_SESSION['gi_allowed'] ?? [];
    if (empty($allowed)) {
        $rbac_clause = " AND 1=0 ";
        $rbac_v_clause = " AND 1=0 ";
    } else {
        $inStrs = [];
        foreach($allowed as $i => $ar) {
            $pname = "rbac_rest_$i";
            $inStrs[] = ":$pname";
            $rbac_params[$pname] = $ar;
        }
        $rbac_clause = " AND restaurante IN (" . implode(',', $inStrs) . ") ";
        $rbac_v_clause = " AND v.restaurante IN (" . implode(',', $inStrs) . ") ";
    }
}

// Ensure the chosen filter is valid for this user
if (!empty($restaurante_filter) && !can_access_restaurant($restaurante_filter)) {
    $restaurante_filter = ''; 
    $where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
    if (!empty($mesero_filter)) {
        $where_clause .= " AND mesero = :mesero";
    }
}

$where_clause .= $rbac_clause;
$params = array_merge($params, $rbac_params);'''
)

code = code.replace(
'''$mesero_query = "SELECT DISTINCT mesero FROM restaurantes_ventas";
$mesero_params = [];
if (!empty($restaurante_filter)) {
    $mesero_query .= " WHERE restaurante = :rest";
    $mesero_params['rest'] = $restaurante_filter;
}
$mesero_query .= " ORDER BY mesero ASC";''',
'''$mesero_query = "SELECT DISTINCT mesero FROM restaurantes_ventas WHERE 1=1 " . $rbac_clause;
$mesero_params = $rbac_params;
if (!empty($restaurante_filter)) {
    $mesero_query .= " AND restaurante = :rest";
    $mesero_params['rest'] = $restaurante_filter;
}
$mesero_query .= " ORDER BY mesero ASC";'''
)

code = code.replace(
'''if (!empty($mesero_filter))
    $mesero_where .= " AND v.mesero = :mesero";
if (!empty($restaurante_filter))
    $mesero_where .= " AND v.restaurante = :restaurante";''',
'''if (!empty($mesero_filter))
    $mesero_where .= " AND v.mesero = :mesero";
if (!empty($restaurante_filter))
    $mesero_where .= " AND v.restaurante = :restaurante";
$mesero_where .= $rbac_v_clause;'''
)

code = code.replace(
'''$top_where = "WHERE fecha >= :start_date AND fecha <= :end_date";
$top_params = ['start_date' => $start_date, 'end_date' => $end_date];
if (!empty($restaurante_filter)) {
    $top_where .= " AND restaurante = :restaurante";
    $top_params['restaurante'] = $restaurante_filter;
}''',
'''$top_where = "WHERE fecha >= :start_date AND fecha <= :end_date" . $rbac_clause;
$top_params = array_merge(['start_date' => $start_date, 'end_date' => $end_date], $rbac_params);
if (!empty($restaurante_filter)) {
    $top_where .= " AND restaurante = :restaurante";
    $top_params['restaurante'] = $restaurante_filter;
}'''
)

code = code.replace(
'''$catalog_where = "WHERE cantidad > 0 AND platillo NOT LIKE 'Unknown%'";
$catalog_params = [];
if (!empty($restaurante_filter)) {
    $catalog_where .= " AND restaurante = :rest";
    $catalog_params['rest'] = $restaurante_filter;
}''',
'''$catalog_where = "WHERE cantidad > 0 AND platillo NOT LIKE 'Unknown%'" . $rbac_clause;
$catalog_params = $rbac_params;
if (!empty($restaurante_filter)) {
    $catalog_where .= " AND restaurante = :rest";
    $catalog_params['rest'] = $restaurante_filter;
}'''
)

with open(r'c:\ICOM\Database\dashboard_php\index.php', 'w', encoding='utf-8') as f:
    f.write(code)

print("done patching index.php")
