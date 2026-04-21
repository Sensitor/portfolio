public class VoieDesSoins extends Voie {
    public VoieDesSoins() {
        super("Voie des soins");
        competences.add(new Competence("Soins legers", 1));
        competences.add(new Competence("Soins moderes", 2));
        competences.add(new Competence("Soins de groupe", 3));
        competences.add(new Competence("Guerison", 4));
    }
}
