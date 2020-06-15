class SCHC_RuleManager:

    def __init__(self):
        self.RULE_ID_NOT_COMPRESSED = 250
        self.context = []
        self.MatchingOperators = {
            "ignore": self.mo_ignore,
            "equal": self.mo_equal,
            "match-mapping": self.mo_matchmapping,
            "MSB": self.mo_msb
        }

    def mo_ignore(self, length, fv, tv, cda):
        return True

    def mo_equal(self, length, fv, tv, cda):
        return fv == tv

    def mo_matchmapping(self, length, fv, tv, cda):
        if type(tv) is dict:
            for mappingID, mappingValue in tv.items():
                if mappingValue == fv:
                    return True
            return False
        elif type(tv) is list:
            for mappingValue in tv:
                # print ('\t', type (mappingValue), '  <=> ', type (FV), end='|')
                # print ('\t', mappingValue, '  <=> ', FV)
                if type(mappingValue) != type(fv):
                    return False
                if mappingValue == fv:
                    return True
            return False
        else:
            return False

    def mo_msb(self, length, fv, tv, cda):
        # To Be Defined
        pass

    def get_rule_from_id(self, rule_id):
        for r in self.context:
            if r["ruleid"] == rule_id:
                return r
        print("Rule not found")
        return False

    def add_rule(self, rule):
        """Add a rule to the context, ruleid must be unique """
        added_rule_id = rule["ruleid"]
        for r in self.context:
            if r["ruleid"] == added_rule_id:
                raise ValueError('Rule ID already exists ', added_rule_id)

        self.context.append(rule)

    def find_rule_from_headers(self, headers, direction):

        headers_keys = headers.keys()
        for rule in self.context:
            """Si algún Header del paquete que se está examinando no puede coincidir con un FID de un Field Description,
            la regla DEBE ser ignorada. """
            flag = False
            for header in headers_keys:
                coincidence = False
                for content in rule["content"]:
                    if header[0] == content[0]:
                        coincidence = True
                        break
                if coincidence is False:
                    print("Header \"" + header[0] + "\" not found in Rule ID: " + str(rule["ruleid"]))
                    print("The Rule MUST be disregarded")
                    flag = True
                    break
            if flag:
                continue

            """Si algún Field Description en la Regla tiene un FID que no puede coincidir con uno de los headers del 
            paquete que se está examinando, la Regla DEBE ser ignorada. """
            flag = False
            for content in rule["content"]:
                coincidence = False
                for header in headers_keys:
                    if header[0] == content[0]:
                        coincidence = True
                        break
                if coincidence is False:
                    print("Field ID \"" + content[0] + "\" of the Rule " + str(rule["ruleid"]) + "not found in "
                                                                                                 "Headers List")
                    print("The Rule MUST be disregarded")
                    flag = True
                    break
            if flag:
                continue

            """Si algún header del paquete no puede coincidir con el FID y el DI de un Field Description, 
            la Regla DEBE ser ignorada """
            flag = False
            for header in headers_keys:
                coincidence = False
                for content in rule["content"]:
                    DI = content[3]
                    if header[0] == content[0] and (direction is DI or DI is "Bi"):
                        coincidence = True
                        break
                if coincidence is False:
                    print("Header \"" + header[0] + "\" does not match with FID and DI in the RuleID " +
                          str(rule["ruleid"]))
                    print("The Rule MUST be disregarded")
                    flag = True
                    break
            if flag:
                continue

            """Si algún header del paquete no puede coincidir con el FID, DI y FP de un Field Description, 
            la Regla DEBE ser ignorada """
            flag = False
            for header in headers_keys:
                coincidence = False
                for content in rule["content"]:
                    PO = content[2]
                    DI = content[3]
                    if header[0] == content[0] and (direction is DI or DI is "Bi") and (header[1] is PO):
                        coincidence = True
                        break
                if coincidence is False:
                    print("Header \"" + header[0] + "\" does not match with FID, DI and FP in the RuleID " +
                          str(rule["ruleid"]))
                    print("The Rule MUST be disregarded")
                    flag = True
                    break
            if flag:
                continue

            """Una vez que cada header se ha asociado con un FID, DI y FP, el valor de cada Header se compara con el 
            Valor objetivo correspondiente (TV) almacenado en la Regla para ese header específico, utilizando el 
            operador correspondiente (MO) . Si cada valor del header satisface los correspondientes operadores 
            coincidentes (MO) de una Regla (es decir, todos los resultados de MO son Verdaderos), esa Regla se usa 
            para comprimir el encabezado. De lo contrario, la regla DEBE ser ignorada."""
            # Looking MO
            MO_is_false = False
            for header in headers_keys:
                for content in rule["content"]:
                    # FID = content[0]
                    LENGTH = content[1]
                    PO = content[2]
                    DI = content[3]
                    if header[0] == content[0] and (direction is DI or DI is "Bi") and (header[1] is PO):
                        FV = headers.get(header)[0]
                        TV = content[4]
                        MO = content[5]
                        CDA = content[6]
                        if not self.MatchingOperators.get(MO)(LENGTH, FV, TV, CDA):
                            MO_is_false = True
                            break

            if MO_is_false:
                break
            else:
                return rule["ruleid"]

        return 250   # Esta Rule no debe existir, es para indicar que el paquete se envia sin comprimir
